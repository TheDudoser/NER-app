import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, Form, File, Depends, Query
from sqlmodel import Session, select
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from src.analysis.tfidf import search_phrases_with_tfidf, search_sentences_in_text_with_tfidf
from config import logger, ANALYSIS_DIR
from database import get_session
from src.database.models import Dictionary, PhraseType
from src.analysis.consts import PATTERN_COLOR
from src.analysis.phrase_extractor import PhraseExtractor

views_router = APIRouter(tags=["views"], default_response_class=HTMLResponse)
templates = Jinja2Templates(directory="templates")
phrase_extractor = PhraseExtractor()

# Фильтр для форматирования даты
templates.env.filters["datetimeformat"] = lambda value: value.strftime('%H:%M %d.%m.%Y')
templates.env.globals['PhraseType'] = PhraseType


# TODO: Повыносить логику работы с данными в сервисы

@views_router.get("/", name="empty_analyze_text", status_code=status.HTTP_200_OK)
async def read_root(request: Request) -> HTMLResponse:
    """Страница анализа текста"""
    return templates.TemplateResponse("index.html.jinja", {"request": request, "pattern_with_colors": PATTERN_COLOR})


@views_router.post("/", name="analyze_text")
async def analyze_text(
        request: Request,
        text: Optional[str] = Form(None),
        file: UploadFile = File(None)
) -> HTMLResponse:
    """Обработка и отображение заданного для анализа текста"""
    if not text and not file.filename:
        logger.warning(msg="Text or file is empty")
        return templates.TemplateResponse("index.html.jinja", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "error": "Был введён пустой текст или не выбран файл"
        })

    content = text or ""
    if file and file.filename:
        try:
            file_content = (await file.read()).decode("utf-8")
            content = f"{content}\n{file_content}" if content else file_content
        except Exception as e:
            logger.error(msg=f"Error reading file: {str(e)}", exc_info=True)
            return templates.TemplateResponse("index.html.jinja", {
                "request": request,
                "pattern_with_colors": PATTERN_COLOR,
                "error": "Произошла ошибка при чтении файла"
            })

    try:
        analysis = phrase_extractor.analyze_text_with_stats(content)

        for phrase in analysis['phrases']:
            phrase['color'] = PATTERN_COLOR.get(phrase['pattern_type'], 'black')

        return templates.TemplateResponse("index.html.jinja", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "result_analysis": analysis,
            "text_analysis": text
        })

    except Exception as e:
        logger.error(msg=f"Analysis error {str(e)}", exc_info=True)
        return templates.TemplateResponse("index.html.jinja", {
            "request": request,
            "pattern_with_colors": PATTERN_COLOR,
            "error": "Произошла неизвестная ошибка при анализе текста"
        })


@views_router.get("/dictionary/create", name="create_dictionary")
async def create_dictionary(request: Request, analysis_file_id: str) -> HTMLResponse:
    """Страница для создания словаря из сохраненных ранее результатов анализа"""
    try:
        filename = f"{ANALYSIS_DIR}/analysis_{analysis_file_id}.json"
        with open(filename, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

        # Преобразуем данные для шаблона
        phrases = [
            {
                "id": idx,
                "phrase": phrase["phrase"],
                "pattern_type": phrase["pattern_type"],
                "tfidf": phrase["tfidf_score"]
            }
            for idx, phrase in enumerate(analysis_data["phrases"])
        ]

        # 1) Добавляем лемму главного существительного
        for item in phrases:
            item['head_noun'] = phrase_extractor.get_head_noun_lemma(item['phrase'])

        # 2) Сортируем: сначала по head_noun, потом по тексту для стабильности
        phrases.sort(key=lambda x: (x['head_noun'], x['phrase']))

        return templates.TemplateResponse("dictionary.html.jinja", {
            "request": request,
            "phrases": phrases,
            "file_id": analysis_file_id,
            "text": analysis_data['text']
        })
    except Exception as e:
        logger.error(msg=f"Error loading analysis: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html.jinja", {
            "request": request,
            "error": "Произошла ошибка при загрузке файла с результатом анализа"
        })


@views_router.get("/dictionaries", name="list_dictionaries")
async def list_dictionaries(request: Request, db: Session = Depends(get_session)) -> HTMLResponse:
    try:
        # Получаем все словари из БД
        dictionaries = db.exec(select(Dictionary)).all()
        # Собираем данные для шаблона
        dictionaries_data = []
        for dictionary in dictionaries:
            dictionaries_data.append({
                'id': dictionary.id,
                'name': dictionary.name,
                'created_at': dictionary.created_at_local,
                'terms_count': len(dictionary.terms),
                'connections_count': len(dictionary.connections)
            })
        # Сортировка по дате создания (новые - выше)
        dictionaries_data.sort(key=lambda x: x['created_at'], reverse=True)
        return templates.TemplateResponse("dictionaries_list.html.jinja", {
            "request": request,
            "dictionaries": dictionaries_data
        })
    except Exception as e:
        logger.error(msg=f"Error listing dictionaries: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html.jinja", {
            "request": request,
            "error": "Произошла ошибка при загрузке списка словарей"
        })


@views_router.get("/dictionary/{dictionary_id}/edit", name="edit_dictionary")
async def edit_dictionary(request: Request, dictionary_id: int, db: Session = Depends(get_session)) -> HTMLResponse:
    try:
        # Получаем словарь с терминами и связями
        dictionary = db.get(Dictionary, dictionary_id)
        if not dictionary:
            raise Exception("Словарь не найден")
        # Формируем данные терминов для шаблона
        dict_terms = []
        for term in dictionary.terms:
            dict_terms.append({
                'id': term.id,
                'phrase': term.text,
                'pattern_type': term.type,
                'phrase_type': term.phrase_type.value,
                'head_noun': phrase_extractor.get_head_noun_lemma(term.text),
                'tfidf': term.tfidf,
            })

        # Сортировка терминов
        dict_terms.sort(key=lambda x: (x['head_noun'], x['phrase']))
        # Формируем данные связей
        connections = [
            {'from': conn.from_term_id, 'to': conn.to_term_id}
            for conn in dictionary.connections
        ]
        # TODO: dictionary_data можно будет упростить или вовсе избавиться
        # Собираем итоговый словарь для шаблона
        dictionary_data = {
            'id': dictionary.id,
            'name': dictionary.name,
            'phrases': [t for t in dict_terms if t['phrase_type'] == PhraseType.phrase],
            'terms': [t for t in dict_terms if t['phrase_type'] == PhraseType.term],
            'synonyms': [t for t in dict_terms if t['phrase_type'] == PhraseType.synonym],
            'definitions': [t for t in dict_terms if t['phrase_type'] == PhraseType.definition],
            'connections': connections,
            'tfidf_range': dictionary.tfidf_range
        }

        return templates.TemplateResponse("dictionary.html.jinja", {
            "request": request,
            "dictionary": dictionary,
            "dictionary_data": dictionary_data,
            "is_edit_mode": True,
            "tfidf_range": dictionary.tfidf_range
        })
    except Exception as e:
        logger.error(msg=f"Error loading dictionary: {str(e)}", exc_info=True)
        return templates.TemplateResponse("error.html.jinja", {
            "request": request,
            "error": f"Произошла ошибка при загрузке словаря"
        })


@views_router.get("/search", name="search")
async def search(
        request: Request,
        query: Optional[str] = Query(None),
        db: Session = Depends(get_session)
) -> HTMLResponse:
    result = []
    if (query is not None) and (query != ""):
        dictionaries = db.exec(
            select(Dictionary)
            .order_by(Dictionary.updated_at)
            .limit(3)
        ).all()

        for dictionary in dictionaries:
            dict_entry = {
                'dictionary': dictionary,
                'terms': []
            }

            # 1. Ищем все подходящие термины.
            # Вытягивает только не скрытые термины.
            #   Можно было бы сделать это в запросе, но я так и не разобрался как нормально это сделать...
            dict_terms = [t for t in dictionary.terms if t.hidden is False]
            terms_with_sims = search_phrases_with_tfidf(query=query, phrases=dict_terms)
            print(terms_with_sims)

            for term, sim in terms_with_sims:
                term_entry = {
                    'term': term,
                    'similarity': sim,
                    'sentences': []
                }
                # 2. Поиск термина во всех текстах словаря
                for document in dictionary.documents:
                    if document.content == '':
                        continue
                    sentences = search_sentences_in_text_with_tfidf(
                        query=term.text,
                        text=document.content
                    )
                    term_entry['sentences'] = term_entry['sentences'] + sentences
                dict_entry['terms'].append(term_entry)
            result.append(dict_entry)

        print(result)
    return templates.TemplateResponse("search.html.jinja", {
        "request": request,
        "search_results": result
    })
