-- Modelo operacional do assistente da revendedora.
-- Quantidades usam o prefixo qt_. O vetor do catálogo já nasce aqui
-- para a fase 2 só inserir linhas. nr_cpf não deve ser lido por tool.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE revendedora (
    id_revendedora integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nm_revendedora text NOT NULL UNIQUE,
    nr_cpf text NOT NULL UNIQUE
);

COMMENT ON COLUMN revendedora.nr_cpf IS
    'Dado pessoal. Nenhuma tool deve selecionar esta coluna.';

CREATE TABLE ciclo (
    id_ciclo integer PRIMARY KEY,
    nm_ciclo text NOT NULL,
    fl_vigente boolean NOT NULL DEFAULT false
);

CREATE UNIQUE INDEX ciclo_um_vigente
    ON ciclo ((true))
    WHERE fl_vigente;

CREATE TABLE produto (
    id_produto integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cd_sku text NOT NULL UNIQUE,
    nm_produto text NOT NULL UNIQUE,
    nm_marca text NOT NULL CHECK (nm_marca IN ('Boticário', 'Eudora'))
);

CREATE TABLE estoque (
    id_produto integer PRIMARY KEY REFERENCES produto (id_produto),
    qt_disponivel integer NOT NULL CHECK (qt_disponivel >= 0)
);

COMMENT ON TABLE estoque IS
    'Saldo único do centro de distribuição. Igual para todas as revendedoras.';

CREATE TABLE pedido (
    id_pedido integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_revendedora integer NOT NULL REFERENCES revendedora (id_revendedora),
    id_ciclo integer NOT NULL REFERENCES ciclo (id_ciclo),
    dt_pedido date NOT NULL,
    des_status text NOT NULL CHECK (
        des_status IN ('faturado', 'em trânsito', 'entregue', 'cancelado')
    ),
    nm_transportadora text
);

CREATE INDEX pedido_revendedora_data
    ON pedido (id_revendedora, dt_pedido DESC);

CREATE TABLE item_pedido (
    id_pedido integer NOT NULL REFERENCES pedido (id_pedido),
    id_produto integer NOT NULL REFERENCES produto (id_produto),
    qt_item integer NOT NULL CHECK (qt_item > 0),
    vl_preco numeric(10, 2) NOT NULL CHECK (vl_preco >= 0),
    PRIMARY KEY (id_pedido, id_produto)
);

CREATE TABLE margem (
    id_revendedora integer NOT NULL REFERENCES revendedora (id_revendedora),
    id_ciclo integer NOT NULL REFERENCES ciclo (id_ciclo),
    vl_margem numeric(5, 2) NOT NULL,
    PRIMARY KEY (id_revendedora, id_ciclo)
);

COMMENT ON COLUMN margem.vl_margem IS
    'Percentual de lucratividade da revendedora no ciclo. Ex.: 18 significa 18%.';

CREATE TABLE sessao (
    id_sessao text PRIMARY KEY,
    id_revendedora integer NOT NULL REFERENCES revendedora (id_revendedora),
    dt_criacao timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE catalogo_chunk (
    id_chunk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    des_conteudo text NOT NULL,
    embedding vector(768),
    nm_arquivo text NOT NULL,
    nr_pagina integer
);
