"""Trace de uma mensagem no Langfuse.

Sem as duas chaves, nenhuma função abre cliente e o grafo responde igual.
O nome da revendedora não entra no trace. CPF, e-mail e telefone são
trocados pela mesma máscara da saída antes de sair da máquina.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from app.guardrails import mascarar_saida

ConcluirBusca = Callable[..., None]


def _carregar_env() -> None:
    """Lê o .env da raiz quando a variável ainda não está no processo."""
    if "pytest" in sys.modules:
        return
    caminho = Path(__file__).resolve().parents[1] / ".env"
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        chave, _, valor = texto.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and chave not in os.environ:
            os.environ[chave] = valor


_carregar_env()


def ligada() -> bool:
    publica = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secreta = os.environ.get("LANGFUSE_SECRET_KEY")
    return bool(publica and secreta)


def atributos_mascarados(atributos: dict) -> dict:
    """Devolve só as chaves cujo texto mudou depois da máscara."""
    ajustes: dict = {}
    for chave, valor in atributos.items():
        if not isinstance(valor, str):
            continue
        limpo = mascarar_saida(valor)
        if limpo != valor:
            ajustes[chave] = limpo
    return ajustes


def mascarar_spans(*, params):
    from langfuse.types import MaskOtelSpansResult, OtelSpanPatch

    patches = {}
    for identificador, span in params.spans.items():
        ajustes = atributos_mascarados(dict(span.attributes))
        if ajustes:
            patches[identificador] = OtelSpanPatch(set_attributes=ajustes)
    if not patches:
        return None
    return MaskOtelSpansResult(span_patches=patches)


def _mascara_sdk(*, data, **kwargs):
    if isinstance(data, str):
        return mascarar_saida(data)
    if isinstance(data, dict):
        return {chave: _mascara_sdk(data=valor) for chave, valor in data.items()}
    if isinstance(data, list):
        return [_mascara_sdk(data=item) for item in data]
    return data


_cliente = None


def cliente():
    global _cliente
    if _cliente is None:
        from langfuse import Langfuse

        _cliente = Langfuse(mask=_mascara_sdk, mask_otel_spans=mascarar_spans)
    return _cliente


def callback():
    from langfuse.langchain import CallbackHandler

    return CallbackHandler()


def propagar(**kwargs):
    from langfuse import propagate_attributes

    return propagate_attributes(**kwargs)


class Rastreio:
    def __init__(self, config: dict):
        self.config = config
        self.resposta = ""


def _anotar(nome: str, metadata: dict, *, tipo: str = "span") -> None:
    if not ligada():
        return
    try:
        with cliente().start_as_current_observation(
            as_type=tipo,
            name=nome,
            metadata=metadata,
        ):
            return
    except Exception:
        return


def anotar_roteamento(intencao_modelo: str, intencao_ajustada: str) -> None:
    _anotar(
        "roteamento",
        {
            "intencao_modelo": intencao_modelo,
            "intencao_ajustada": intencao_ajustada,
        },
    )


def anotar_ferramenta(escolha: str, qt_linhas: int) -> None:
    _anotar(
        "ferramenta",
        {"ferramenta": escolha, "qt_linhas": qt_linhas},
        tipo="tool",
    )


def anotar_mascara(alterou: bool) -> None:
    _anotar("mascarar", {"mascara_alterou": alterou}, tipo="guardrail")


@contextmanager
def observar_busca(pergunta: str) -> Iterator[ConcluirBusca]:
    """Marca a busca do catálogo. O vetor não entra no trace."""
    if not ligada():
        yield lambda **kwargs: None
        return
    try:
        contexto = cliente().start_as_current_observation(
            as_type="embedding",
            name="buscar_catalogo",
            input={"pergunta": pergunta},
        )
        span = contexto.__enter__()
    except Exception:
        yield lambda **kwargs: None
        return

    def concluir(*, qt_trechos: int) -> None:
        try:
            span.update(
                output={"qt_trechos": qt_trechos},
                metadata={"qt_trechos": qt_trechos},
            )
        except Exception:
            return

    try:
        yield concluir
    finally:
        contexto.__exit__(None, None, None)


@contextmanager
def tracar_mensagem(*, id_revendedora: int, id_sessao: str, mensagem: str) -> Iterator[Rastreio]:
    config: dict = {"configurable": {"thread_id": id_sessao}}
    rastreio = Rastreio(config)
    if not ligada():
        yield rastreio
        return

    span = None
    contexto = None
    propagacao = None
    try:
        contexto = cliente().start_as_current_observation(
            as_type="span",
            name="mensagem",
            input={"mensagem": mensagem},
        )
        span = contexto.__enter__()
        propagacao = propagar(
            user_id=str(id_revendedora),
            session_id=id_sessao,
            trace_name="assistente",
        )
        propagacao.__enter__()
        config["callbacks"] = [callback()]
        config["metadata"] = {
            "langfuse_user_id": str(id_revendedora),
            "langfuse_session_id": id_sessao,
            "langfuse_tags": ["assistente"],
        }
        config["run_name"] = "assistente"
    except Exception:
        _descartar(contexto, propagacao)
        config.pop("callbacks", None)
        config.pop("metadata", None)
        config.pop("run_name", None)
        span = None

    try:
        yield rastreio
    finally:
        if span is not None:
            _fechar_mensagem(contexto, propagacao, span, rastreio)


def _descartar(contexto, propagacao) -> None:
    try:
        if propagacao is not None:
            propagacao.__exit__(None, None, None)
    except Exception:
        pass
    try:
        if contexto is not None:
            contexto.__exit__(None, None, None)
    except Exception:
        pass


def _fechar_mensagem(contexto, propagacao, span, rastreio: Rastreio) -> None:
    try:
        span.update(output={"resposta": rastreio.resposta})
    except Exception:
        pass
    try:
        if propagacao is not None:
            propagacao.__exit__(None, None, None)
    except Exception:
        pass
    try:
        if contexto is not None:
            contexto.__exit__(None, None, None)
    except Exception:
        pass
    try:
        cliente().flush()
    except Exception:
        pass
