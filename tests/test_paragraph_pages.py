"""paragraph_pages() — 문단별 시작 쪽 (전역 1-based) 계약 테스트."""

import pytest

import rhwp


def test_length_matches_paragraphs(hwp_sample):
    """반환 길이 == paragraph_count == len(paragraphs()) — 평탄화 1:1 계약."""
    doc = rhwp.parse(hwp_sample)
    pages = doc.paragraph_pages()
    assert len(pages) == doc.paragraph_count == len(doc.paragraphs())


def test_pages_are_monotonic_and_in_range(hwp_sample):
    """쪽은 비감소(문단은 문서 순서)이고 1..=page_count 안이다."""
    doc = rhwp.parse(hwp_sample)
    pages = doc.paragraph_pages()
    assert all(1 <= p <= doc.page_count for p in pages)
    assert all(a <= b for a, b in zip(pages, pages[1:]))


def test_multipage_document_spans_pages(hwp_sample):
    """여러 쪽 문서면 마지막 문단들은 뒤쪽 쪽에 배정된다 (전부 1쪽이면 회귀)."""
    doc = rhwp.parse(hwp_sample)
    pages = doc.paragraph_pages()
    if doc.page_count > 1:
        assert max(pages) > 1


def test_paragraph_text_is_on_its_page(hwp_sample):
    """교차 검증: 문단 텍스트가 실제로 그 쪽의 PDF 렌더에 나타난다.

    SVG 는 글리프가 개별 배치되어 문자열 대조가 안 되므로 PDF 텍스트 레이어로
    검사한다 (pymupdf 필요 — 없으면 skip). 문단 머리 20자가 문서에서 유일하게
    나타나는 문단만 검사해 오탐을 막고, 그 문단의 배정 쪽에 머리가 있어야 한다.
    """
    fitz = pytest.importorskip("fitz")
    doc = rhwp.parse(hwp_sample)
    pages = doc.paragraph_pages()
    paras = doc.paragraphs()
    pdf = fitz.open(stream=doc.render_pdf(), filetype="pdf")
    flats = ["".join(pdf[i].get_text().split()) for i in range(pdf.page_count)]
    pdf.close()
    checked = mismatched = 0
    for text, page in zip(paras, pages):
        head = "".join(text.split())[:20]
        if len(head) < 20:
            continue
        where = [i + 1 for i, f in enumerate(flats) if head in f]
        if len(where) != 1:
            continue                       # 지면에 없거나(렌더 표기 차이) 여러 쪽 — 판정 제외
        checked += 1
        if page != where[0]:
            mismatched += 1
    assert checked >= 10, "판정 가능한 문단이 너무 적다 (%d)" % checked
    assert mismatched == 0, "배정 쪽과 지면 실측이 %d/%d건 불일치" % (mismatched, checked)


def test_hwpx_supported(hwpx_sample):
    """HWPX 도 같은 계약."""
    doc = rhwp.parse(hwpx_sample)
    pages = doc.paragraph_pages()
    assert len(pages) == doc.paragraph_count
    assert all(1 <= p <= doc.page_count for p in pages)
