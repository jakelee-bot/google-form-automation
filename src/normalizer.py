import os
from dotenv import load_dotenv

load_dotenv()


def normalize_email_text(raw: str) -> str:
    """Optionally normalize raw email text into strict `Key: Value` lines using OpenAI.

    - If `OPENAI_API_KEY` is not set or the OpenAI SDK is unavailable, returns input unchanged.
    - Output must use EXACT labels in the specified order, one per line, no extra commentary.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    
    print(f"\n=== NORMALIZER DEBUG ===")
    print(f"API Key found: {bool(api_key)}")
    print(f"API Key starts with: {api_key[:10] + '...' if api_key else 'None'}")
    print(f"Raw text length: {len(raw) if raw else 0}")
    
    if not api_key or not raw or not raw.strip():
        print("Returning original text (no API key or empty input)")
        return raw

    try:
        # Lazy import to avoid hard dependency when not used
        from openai import OpenAI
        print("OpenAI import successful")
        
        client = OpenAI(api_key=api_key)
        print("OpenAI client created")

        system = (
            "You normalize messy emails into strict 'Key: Value' lines for a downstream parser. "
            "Output ONLY the lines below, in this exact order, one per line, with these exact labels and punctuation. "
            "If a value is unknown, leave it blank after the colon. Do not add any extra text.\n\n"
            "Your name:\n"
            "Your email:\n"
            "Alternate email (optional; if the quote should be sent elsewhere):\n"
            "Organization name:\n"
            "Organization sector (Academic or Industry):\n"
            "How many people need Premium access?:\n"
            "Length of license (in years):\n"
            "Name of institution, enterprise, lab, or team (optional; leave blank to use your organization name):\n"
            "Names and emails of intended users (optional; leave blank to use your own email or if it is a license just for yourself):\n"
            "Admin name (optional; leave blank to use your name):\n"
            "Admin email (optional; leave blank to use your email):\n"
            "Billing name (optional):\n"
            "Billing email (optional):\n"
            "Billing address (optional):\n"
            "Shipping address (optional):\n"
            "VAT or Tax ID number (optional):"
        )

        user = (
            "Normalize the following email. Return ONLY the 16 lines above, exactly once each, in order, filled with values. If a field is missing, keep the label and a trailing colon with nothing after it.\n\n"
            + raw
        )

        print("Calling OpenAI API...")
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            max_tokens=700,
        )

        content = resp.choices[0].message.content if resp.choices else None
        print(f"OpenAI response received: {bool(content)}")
        
        if not content:
            print("No content in OpenAI response, returning original")
            return raw

        # Ensure we only return the lines (some models can add surrounding whitespace)
        result = content.strip()
        print(f"Returning normalized text (length: {len(result)})")
        return result
    except Exception as e:
        print(f"OpenAI error: {str(e)}")
        # Fail open to original raw text on any error
        return raw
