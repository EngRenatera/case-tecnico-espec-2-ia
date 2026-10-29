"""O trace só sai quando as duas chaves existem. Sem elas, o grafo não muda."""

from contextlib import contextmanager, nullcontext

from app.graph import invocar
from app.observabilidade import (
    anotar_ferramenta,
    anotar_mascara,
    anotar_roteamento,
    atributos_mascarados,
)


class _Grafo:
    def __init__(self, resposta: str = "ok"):
        self.config = None
        self._resposta = resposta

    def invoke(self, entrada, config):
        self.config = config
        self.entrada = entrada

    def get_state(self, config):
        class _Estado:
            values = {"resposta": self._resposta}

        return _Estado()


class _Span:
    def __init__(self, eventos: list):
        self._eventos = eventos

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def update(self, **kwargs):
        self._eventos.append(("update", kwargs))


class _Cliente:
    def __init__(self):
        self.eventos: list = []

    def start_as_current_observation(self, **kwargs):
        self.eventos.append(("abrir", kwargs))
        return _Span(self.eventos)

    def flush(self):
        self.eventos.append("flush")


def _sem_chaves(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)


def _com_chaves(monkeypatch, cliente: _Cliente):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr("app.observabilidade.cliente", lambda: cliente)
    monkeypatch.setattr("app.observabilidade.callback", lambda: "handler")
    monkeypatch.setattr("app.observabilidade.propagar", lambda **kwargs: nullcontext())


def test_invocar_sem_chaves_nao_poe_callback(monkeypatch):
    _sem_chaves(monkeypatch)
    grafo = _Grafo()

    estado = invocar(grafo, id_revendedora=1, id_sessao="sessao-1", mensagem="oi")

    assert estado["resposta"] == "ok"
    assert "callbacks" not in grafo.config
    assert grafo.config["configurable"]["thread_id"] == "sessao-1"


def test_invocar_com_chaves_poe_callback_sessao_e_resposta(monkeypatch):
    cliente = _Cliente()
    _com_chaves(monkeypatch, cliente)
    grafo = _Grafo(resposta="a margem é 18")

    invocar(grafo, id_revendedora=1, id_sessao="sessao-1", mensagem="qual a minha margem?")

    assert grafo.config["callbacks"] == ["handler"]
    assert grafo.config["configurable"]["thread_id"] == "sessao-1"
    assert grafo.config["run_name"] == "assistente"
    assert grafo.config["metadata"]["langfuse_user_id"] == "1"
    assert grafo.config["metadata"]["langfuse_session_id"] == "sessao-1"
    assert "nm_revendedora" not in str(grafo.config)
    assert cliente.eventos[0][0] == "abrir"
    assert cliente.eventos[0][1]["name"] == "mensagem"
    assert ("update", {"output": {"resposta": "a margem é 18"}}) in cliente.eventos
    assert "flush" in cliente.eventos


def test_anotar_roteamento_sem_chaves_nao_abre_cliente(monkeypatch):
    _sem_chaves(monkeypatch)

    def cliente():
        raise AssertionError("cliente")

    monkeypatch.setattr("app.observabilidade.cliente", cliente)
    anotar_roteamento("bloqueado", "pedido")


def test_anotar_roteamento_grava_intencao_crua_e_ajustada(monkeypatch):
    cliente = _Cliente()
    _com_chaves(monkeypatch, cliente)

    anotar_roteamento("bloqueado", "pedido")

    abertura = cliente.eventos[0][1]
    assert abertura["name"] == "roteamento"
    assert abertura["metadata"]["intencao_modelo"] == "bloqueado"
    assert abertura["metadata"]["intencao_ajustada"] == "pedido"


def test_anotar_ferramenta_grava_escolha_e_contagem(monkeypatch):
    cliente = _Cliente()
    _com_chaves(monkeypatch, cliente)

    anotar_ferramenta("estoque", 1)

    meta = cliente.eventos[0][1]["metadata"]
    assert cliente.eventos[0][1]["name"] == "ferramenta"
    assert meta["ferramenta"] == "estoque"
    assert meta["qt_linhas"] == 1


def test_anotar_mascara_registra_o_flag_sem_o_texto(monkeypatch):
    cliente = _Cliente()
    _com_chaves(monkeypatch, cliente)

    anotar_mascara(True)

    assert cliente.eventos[0][1]["metadata"] == {"mascara_alterou": True}
    assert "529.982.247-25" not in str(cliente.eventos)


def test_busca_abre_observacao_sem_gravar_o_vetor(monkeypatch):
    registros = []

    @contextmanager
    def observar(pergunta):
        caixa: dict = {}

        def concluir(**kwargs):
            caixa.update(kwargs)
            registros.append((pergunta, dict(caixa)))

        yield concluir

    class _Conn:
        def execute(self, *args, **kwargs):
            class _Resultado:
                def fetchall(self):
                    return [("trecho da promoção",)]

            return _Resultado()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("app.rag.observar_busca", observar)
    monkeypatch.setattr("app.rag.embed", lambda textos: [[0.0] * 768])
    monkeypatch.setattr("app.rag.psycopg.connect", lambda *args, **kwargs: _Conn())

    from app.rag import buscar_catalogo

    assert buscar_catalogo("promoção") == ["trecho da promoção"]
    assert registros == [("promoção", {"qt_trechos": 1})]


def test_falha_do_cliente_nao_impede_a_resposta(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    def cliente():
        raise RuntimeError("langfuse fora")

    monkeypatch.setattr("app.observabilidade.cliente", cliente)
    grafo = _Grafo()

    estado = invocar(grafo, id_revendedora=1, id_sessao="sessao-1", mensagem="oi")

    assert estado["resposta"] == "ok"
    assert "callbacks" not in grafo.config


def test_mascara_do_sdk_recebe_data():
    from app.observabilidade import _mascara_sdk

    assert _mascara_sdk(data="cpf 529.982.247-25") == "cpf [cpf]"
    assert _mascara_sdk(data={"texto": "cpf 529.982.247-25"}) == {"texto": "cpf [cpf]"}


def test_mascarar_spans_troca_cpf_e_ignora_texto_limpo():
    from types import SimpleNamespace

    from app.observabilidade import mascarar_spans

    sujo = ("trace", "sujo")
    limpo = ("trace", "limpo")
    params = SimpleNamespace(
        spans={
            sujo: SimpleNamespace(attributes={"gen_ai.completion": "cpf 529.982.247-25"}),
            limpo: SimpleNamespace(attributes={"modelo": "qwen"}),
        }
    )

    resultado = mascarar_spans(params=params)

    assert resultado.span_patches[sujo].set_attributes == {
        "gen_ai.completion": "cpf [cpf]"
    }
    assert limpo not in resultado.span_patches


def test_atributos_mascarados_troca_cpf_no_texto_exportado():
    saida = atributos_mascarados({"gen_ai.completion": "cpf 529.982.247-25"})

    assert saida == {"gen_ai.completion": "cpf [cpf]"}
    assert atributos_mascarados({"modelo": "qwen"}) == {}
