import re


KNOWN_BRANDS = {
    "apple",
    "samsung",
    "xiaomi",
    "redmi",
    "oneplus",
    "oppo",
    "vivo",
    "realme",
    "motorola",
    "google",
    "sony",
    "nokia",
    "dell",
    "hp",
    "lenovo",
    "asus",
    "acer",
    "msi",
    "microsoft",
    "huawei",
}


DEVICE_SPECIFIC_COMPONENTS = {
    "battery",
    "display",
    "screen",
    "lcd",
    "oled",
    "amoled",
    "motherboard",
    "logic board",
    "mainboard",
    "ram",
    "memory",
    "ssd",
    "hard drive",
    "hdd",
    "camera module",
    "camera",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def detect_brand(value: str | None):
    text = normalize_text(value)

    for brand in KNOWN_BRANDS:
        if re.search(rf"\b{re.escape(brand)}\b", text):
            return brand

    return None


def is_device_specific_component(part_name: str | None) -> bool:
    text = normalize_text(part_name)

    for component in DEVICE_SPECIFIC_COMPONENTS:
        if re.search(rf"\b{re.escape(component)}\b", text):
            return True

    return False


def check_component_product_mismatch(
    product_name,
    product_brand,
    product_model,
    part_name,
):
    result = {
        "fraud_detected": False,
        "flag": None,
        "severity": "LOW",
        "product_brand": None,
        "component_brand": None,
        "component_type_specific": False,
    }

    if not part_name:
        return result

    component_specific = is_device_specific_component(part_name)

    result["component_type_specific"] = component_specific

    if not component_specific:
        return result

    product_brand_detected = detect_brand(product_brand)

    if not product_brand_detected:
        product_brand_detected = detect_brand(product_name)

    component_brand_detected = detect_brand(part_name)

    result["product_brand"] = product_brand_detected
    result["component_brand"] = component_brand_detected

    if not product_brand_detected:
        return result

    if not component_brand_detected:
        return result

    if product_brand_detected == component_brand_detected:
        return result

    result["fraud_detected"] = True
    result["severity"] = "HIGH"

    result["flag"] = (
        f"Possible component-product mismatch: "
        f"{component_brand_detected.title()} component "
        f"'{part_name}' recorded for "
        f"{product_brand_detected.title()} product."
    )

    return result


def check_document_content(
    document_text: str,
    product_name: str | None,
    product_brand: str | None,
    product_model: str | None,
    part_name: str | None = None,
    part_serial: str | None = None,
):
    """
    Validate the ACTUAL CONTENT of an uploaded document.

    The filename is intentionally NOT used.

    Checks:
    1. Brand mentioned inside the document
    2. Product model mentioned inside the document
    3. Component type mentioned inside the document
    4. Component serial number mentioned inside the document
    """

    result = {
        "fraud_detected": False,
        "severity": "LOW",
        "flags": [],
        "document_brand": None,
        "document_contains_product_model": None,
        "document_contains_component": None,
        "document_contains_serial": None,
    }

    text = normalize_text(document_text)

    if not text:
        result["flags"].append(
            {
                "type": "DOCUMENT_CONTENT_UNREADABLE",
                "severity": "MEDIUM",
                "message": (
                    "The document was uploaded, but readable text "
                    "could not be extracted from its content."
                ),
            }
        )

        result["fraud_detected"] = True
        result["severity"] = "MEDIUM"

        return result

    # ---------------------------------------------------------
    # 1. BRAND CHECK
    # ---------------------------------------------------------

    document_brand = detect_brand(text)

    result["document_brand"] = document_brand

    expected_brand = detect_brand(product_brand)

    if not expected_brand:
        expected_brand = detect_brand(product_name)

    if (
        document_brand
        and expected_brand
        and document_brand != expected_brand
    ):
        result["flags"].append(
            {
                "type": "DOCUMENT_PRODUCT_BRAND_MISMATCH",
                "severity": "HIGH",
                "message": (
                    f"Document content mentions "
                    f"{document_brand.title()}, but the registered "
                    f"product is {expected_brand.title()}."
                ),
            }
        )

    # ---------------------------------------------------------
    # 2. PRODUCT MODEL CHECK
    # ---------------------------------------------------------

    if product_model:
        normalized_model = normalize_text(product_model)

        model_found = normalized_model in text

        result["document_contains_product_model"] = model_found

        # We do NOT mark missing model as fraud because
        # many genuine invoices do not contain the exact model.
        #
        # We only use this as supporting evidence.

    # ---------------------------------------------------------
    # 3. COMPONENT CHECK
    # ---------------------------------------------------------

    if part_name:
        normalized_part = normalize_text(part_name)

        component_keywords = [
            "battery",
            "display",
            "screen",
            "lcd",
            "oled",
            "amoled",
            "motherboard",
            "logic board",
            "mainboard",
            "ram",
            "memory",
            "ssd",
            "hard drive",
            "hdd",
            "camera",
            "camera module",
        ]

        detected_component = None

        for component in component_keywords:
            if component in normalized_part:
                detected_component = component
                break

        if detected_component:
            component_found = detected_component in text

            result["document_contains_component"] = component_found

            if not component_found:
                result["flags"].append(
                    {
                        "type": "DOCUMENT_COMPONENT_MISMATCH",
                        "severity": "HIGH",
                        "message": (
                            f"Recorded component '{part_name}' "
                            f"was not found in the document content."
                        ),
                    }
                )

    # ---------------------------------------------------------
    # 4. COMPONENT SERIAL CHECK
    # ---------------------------------------------------------

    if part_serial:
        normalized_serial = normalize_text(part_serial)
        serial_found = normalized_serial in text
        result["document_contains_serial"] = serial_found

    # Missing serial alone is NOT considered fraud.
    # A document may legitimately not contain the component serial.

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    if result["flags"]:
        result["fraud_detected"] = True

        severities = {
            flag["severity"]
            for flag in result["flags"]
        }

        if "HIGH" in severities:
            result["severity"] = "HIGH"
        elif "MEDIUM" in severities:
            result["severity"] = "MEDIUM"

    return result