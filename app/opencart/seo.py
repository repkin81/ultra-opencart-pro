import re
from .schemas import SeoGenerateRequest, SeoGenerateResponse


def slugify(value: str) -> str:
    value = value.lower().strip().replace("ё", "е")
    value = re.sub(r"[^a-zа-я0-9]+", "-", value, flags=re.IGNORECASE)
    return value.strip("-")


def generate_seo(payload: SeoGenerateRequest) -> SeoGenerateResponse:
    pn = f" Артикул {payload.part_number}" if payload.part_number else ""
    models = ", ".join(payload.compatible_models[:8])
    compatibility = f" Совместимость: {models}." if models else ""
    title = f"{payload.product_name}{pn} | Xerox"
    description = f"{payload.product_name}.{compatibility} Подбор и поставка запчастей и расходных материалов для цифровой печати Xerox.{pn}"
    keywords = payload.keywords + payload.compatible_models + ["Xerox", payload.product_name]
    meta_title = title[:70]
    meta_description = description[:160]
    return SeoGenerateResponse(
        title=title,
        description=description,
        meta_title=meta_title,
        meta_description=meta_description,
        meta_keyword=", ".join(dict.fromkeys(k for k in keywords if k))[:500],
        slug=slugify(f"{payload.product_name}-{payload.part_number}"),
    )
