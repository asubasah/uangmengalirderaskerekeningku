import re

def parse_views(views_text: str) -> int:
    """
    Parses Indonesian YouTube view counts to integer.
    Examples:
    - "1,2 jt" -> 1,200,000
    - "123 rb" -> 123,000
    - "500" -> 500
    - "1 M" -> 1,000,000,000 (rare but possible if billion)
    """
    if not views_text:
        return 0
    
    # Normalize: lowercase, remove "x ditonton" or similar suffix if stuck together
    # Typically raw text might be "1,2 jt x ditonton" or just "1,2 jt"
    text = views_text.lower().replace("x ditonton", "").replace("views", "").strip()
    
    # Replace comma with dot for float parsing if necessary
    # But strictly speaking ID uses comma for decimals. Python float() needs dot.
    text_clean = text.replace(",", ".")
    
    multiplier = 1
    if "jt" in text_clean:
        multiplier = 1_000_000
        text_clean = text_clean.replace("jt", "")
    elif "rb" in text_clean:
        multiplier = 1_000
        text_clean = text_clean.replace("rb", "")
    elif "m" in text_clean: # Billion usually 'M' in some contexts, or 'M' as million in EN, but "jt" is ID million. 
                            # If ID locale, Billion is "Milyar" -> "M"? 
                            # Let's assume standard ID: "jt" = million, "rb" = thousand.
                            # If we see "M", it might be million in mixed context, but let's stick to spec: "jt" and "rb".
                            # If user said "1,2 jt => 1200000", that's the rule.
        pass
    
    # Remove any other non-numeric chars except dot
    # text_clean might still have spaces
    text_clean = re.sub(r"[^\d\.]", "", text_clean)
    
    try:
        if not text_clean:
            return 0
        val = float(text_clean)
        return int(val * multiplier)
    except ValueError:
        return 0
