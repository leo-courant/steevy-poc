"""End-to-end check of the Thales LLM setup. Run from the repo root:

    python scripts/test_thales_llm.py

Fails fast (no retries) and prints the real error if something is wrong.
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))

from config import settings  # noqa: E402
from agent.thales_integration import build_thales_chat_model  # noqa: E402


def main() -> int:
    print(f"base_url : {settings.thales_base_url}")
    print(f"model    : {settings.thales_chat_model}")
    print(f"proxy    : {settings.thales_proxy or '(aucun)'}")
    print(f"CA bundle: {settings.thales_ca_bundle} "
          f"({'trouvé' if Path(settings.thales_ca_bundle).exists() else 'INTROUVABLE'})")
    print(f"API key  : {'définie' if settings.thales_api_key else 'MANQUANTE'}")
    print("-" * 40)

    llm = build_thales_chat_model(settings)
    llm.max_retries = 0
    llm.request_timeout = 30
    try:
        reply = llm.invoke("Réponds uniquement: pong")
    except Exception:
        print("ECHEC — erreur complète ci-dessous:\n")
        traceback.print_exc()
        return 1
    print(f"SUCCES — réponse du modèle: {reply.content!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
