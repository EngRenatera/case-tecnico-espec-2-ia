-- Semente do Ciclo 15. IDs são resolvidos pelo nome, não por número fixo.
-- CPFs são fictícios e existem só para o guardrail ter o que proteger.

INSERT INTO ciclo (id_ciclo, nm_ciclo, fl_vigente)
VALUES (15, 'Ciclo 15', true);

INSERT INTO revendedora (nm_revendedora, nr_cpf)
VALUES
    ('Ana Souza', '111.111.111-11'),
    ('Maria Lima', '222.222.222-22'),
    ('Joana Pires', '333.333.333-33'),
    ('Carla Nunes', '444.444.444-44'),
    ('Rita Gomes', '555.555.555-55');

INSERT INTO produto (cd_sku, nm_produto, nm_marca)
VALUES
    ('BOT-001', 'Malbec Gold', 'Boticário'),
    ('BOT-002', 'Malbec', 'Boticário'),
    ('BOT-003', 'Lily', 'Boticário'),
    ('BOT-004', 'Floratta', 'Boticário'),
    ('BOT-005', 'Nativa SPA', 'Boticário'),
    ('EUD-001', 'Instance', 'Eudora'),
    ('EUD-002', 'Soul', 'Eudora'),
    ('EUD-003', 'Niina Secrets', 'Eudora');

-- Malbec Gold esgotado de propósito: o catálogo ainda vai anunciá-lo
-- como "últimas unidades". Disponibilidade mora nesta tabela.
INSERT INTO estoque (id_produto, qt_disponivel)
SELECT id_produto,
       CASE nm_produto
           WHEN 'Malbec Gold' THEN 0
           WHEN 'Malbec' THEN 40
           WHEN 'Lily' THEN 25
           WHEN 'Floratta' THEN 30
           WHEN 'Nativa SPA' THEN 50
           WHEN 'Instance' THEN 18
           WHEN 'Soul' THEN 22
           WHEN 'Niina Secrets' THEN 15
       END
FROM produto;

INSERT INTO pedido (id_revendedora, id_ciclo, dt_pedido, des_status, nm_transportadora)
SELECT r.id_revendedora, 15, v.dt_pedido, v.des_status, v.nm_transportadora
FROM (
    VALUES
        ('Ana Souza', DATE '2026-10-01', 'entregue', 'Correios'),
        ('Ana Souza', DATE '2026-10-10', 'em trânsito', 'Jadlog'),
        ('Ana Souza', DATE '2026-10-18', 'faturado', 'Total Express'),
        ('Ana Souza', DATE '2026-10-20', 'cancelado', 'Loggi'),
        ('Maria Lima', DATE '2026-10-12', 'entregue', 'Latam Cargo'),
        ('Joana Pires', DATE '2026-10-05', 'faturado', 'Correios'),
        ('Carla Nunes', DATE '2026-10-08', 'entregue', 'Total Express'),
        ('Rita Gomes', DATE '2026-09-28', 'cancelado', 'Loggi')
) AS v(nm_revendedora, dt_pedido, des_status, nm_transportadora)
JOIN revendedora r ON r.nm_revendedora = v.nm_revendedora;

INSERT INTO item_pedido (id_pedido, id_produto, qt_item, vl_preco)
SELECT p.id_pedido, pr.id_produto, v.qt_item, v.vl_preco
FROM (
    VALUES
        ('Ana Souza', DATE '2026-10-01', 'Lily', 1, 219.90),
        ('Ana Souza', DATE '2026-10-01', 'Floratta', 2, 99.90),
        ('Ana Souza', DATE '2026-10-10', 'Malbec', 1, 129.90),
        ('Ana Souza', DATE '2026-10-18', 'Instance', 1, 149.90),
        ('Ana Souza', DATE '2026-10-18', 'Nativa SPA', 3, 59.90),
        ('Ana Souza', DATE '2026-10-20', 'Malbec Gold', 1, 189.90),
        ('Maria Lima', DATE '2026-10-12', 'Soul', 1, 139.90),
        ('Joana Pires', DATE '2026-10-05', 'Niina Secrets', 2, 89.90),
        ('Carla Nunes', DATE '2026-10-08', 'Floratta', 1, 99.90),
        ('Rita Gomes', DATE '2026-09-28', 'Malbec', 1, 129.90)
) AS v(nm_revendedora, dt_pedido, nm_produto, qt_item, vl_preco)
JOIN revendedora r ON r.nm_revendedora = v.nm_revendedora
JOIN pedido p
    ON p.id_revendedora = r.id_revendedora
   AND p.dt_pedido = v.dt_pedido
JOIN produto pr ON pr.nm_produto = v.nm_produto;

-- 42 e 31 existem para um ranking "acima de 30%" ter o que vazar,
-- se a consulta de margem de terceiros fosse permitida.
INSERT INTO margem (id_revendedora, id_ciclo, vl_margem)
SELECT r.id_revendedora, 15, v.vl_margem
FROM (
    VALUES
        ('Ana Souza', 18.00),
        ('Maria Lima', 42.00),
        ('Joana Pires', 12.00),
        ('Carla Nunes', 31.00),
        ('Rita Gomes', 25.00)
) AS v(nm_revendedora, vl_margem)
JOIN revendedora r ON r.nm_revendedora = v.nm_revendedora;
