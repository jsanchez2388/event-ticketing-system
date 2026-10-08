-- ============================================================
-- BEFORE
--   Baseline straight after sql/seed.sql: wallet 2500.00,
--   ticket type 1012 available 148, 1013 available 98,
--   orders ending at 5015. Scenarios 2 and 3 raise errors on purpose.
-- ============================================================
SELECT
    (SELECT wallet_balance FROM users WHERE user_id = 402) AS wallet,
    (SELECT available_quantity FROM ticket_types
      WHERE ticket_type_id = 1012)                         AS avail_1012,
    (SELECT available_quantity FROM ticket_types
      WHERE ticket_type_id = 1013)                         AS avail_1013,
    (SELECT COUNT(*) FROM orders)                          AS orders,
    (SELECT COUNT(*) FROM order_items)                     AS order_items,
    (SELECT COUNT(*) FROM payments)                        AS payments;


-- ============================================================
-- SCENARIO 1 -- successful purchase
--   Jordan Kim buys 2 x Workshop Admission (1012) at $45.00 = $90.00.
--
--   The two SELECT ... FOR UPDATE statements are the point of the exercise.
--   They lock the wallet row and the inventory row for the rest of the
--   transaction, so a second buyer reaching the same ticket type waits here
--   instead of reading a quantity that is about to change. Without them two
--   sessions could both read available_quantity = 148 and both subtract 2,
--   selling three tickets' worth of inventory for two.
-- ============================================================
BEGIN;

-- Lock the buyer.
SELECT user_id, wallet_balance
FROM users
WHERE user_id = 402
FOR UPDATE;

-- Lock the inventory.
SELECT ticket_type_id, event_id, ticket_name, price, available_quantity,
       minimum_purchase, maximum_purchase
FROM ticket_types
WHERE ticket_type_id = 1012
FOR UPDATE;

-- Header. order_id comes from the identity sequence, which seed.sql advanced
-- past 5015, so this becomes 5016.
INSERT INTO orders (user_id, order_date, status,
                    subtotal, service_fee, tax_amount, total_amount)
VALUES (402, CURRENT_TIMESTAMP, 'completed',
        90.00, 0.00, 0.00, 90.00)
RETURNING order_id, status, total_amount;

-- Line item. currval() reads back the order_id generated one statement ago
-- in this same session.
INSERT INTO order_items (order_id, ticket_type_id, quantity, unit_price)
VALUES (currval(pg_get_serial_sequence('orders', 'order_id')), 1012, 2, 45.00)
RETURNING order_item_id, order_id, ticket_type_id, quantity, unit_price;

-- Draw down inventory. chk_ticket_types_available_quantity rejects this if
-- the row cannot cover it.
UPDATE ticket_types
SET available_quantity = available_quantity - 2
WHERE ticket_type_id = 1012
RETURNING ticket_type_id, total_quantity, available_quantity;

-- Charge the wallet. users_wallet_balance_check rejects an overdraft.
UPDATE users
SET wallet_balance = wallet_balance - 90.00
WHERE user_id = 402
RETURNING user_id, wallet_balance;

INSERT INTO payments (order_id, amount, payment_method, payment_status,
                      transaction_reference, payment_date)
VALUES (currval(pg_get_serial_sequence('orders', 'order_id')),
        90.00, 'Credit Card', 'completed',
        'TXN-DEMO-' || currval(pg_get_serial_sequence('orders', 'order_id')),
        CURRENT_TIMESTAMP)
RETURNING payment_id, order_id, amount, payment_status;

COMMIT;

-- Proof: order 5016 exists with its item and payment, and inventory dropped
-- from 148 to 146.
SELECT o.order_id, o.status, o.total_amount,
       oi.ticket_type_id, oi.quantity, oi.unit_price,
       tt.available_quantity AS avail_now,
       p.payment_status, p.transaction_reference,
       u.wallet_balance
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN ticket_types tt ON tt.ticket_type_id = oi.ticket_type_id
JOIN payments p ON p.order_id = o.order_id
JOIN users u ON u.user_id = o.user_id
WHERE o.order_id = (SELECT MAX(order_id) FROM orders);


-- ============================================================
-- SCENARIO 2 -- oversell is refused, and the whole transaction unwinds
--   Ticket type 1013 has 98 left. This asks for 99.
--
--   The order and its line item are inserted FIRST and succeed. The failure
--   comes later, at the inventory update. That ordering is deliberate: it
--   shows that ROLLBACK discards writes that had already been accepted, not
--   just the statement that failed.
-- ============================================================
BEGIN;

SELECT ticket_type_id, ticket_name, available_quantity
FROM ticket_types
WHERE ticket_type_id = 1013
FOR UPDATE;

-- Succeeds.
INSERT INTO orders (user_id, order_date, status,
                    subtotal, service_fee, tax_amount, total_amount)
VALUES (402, CURRENT_TIMESTAMP, 'completed',
        6435.00, 0.00, 0.00, 6435.00)
RETURNING order_id;

-- Succeeds.
INSERT INTO order_items (order_id, ticket_type_id, quantity, unit_price)
VALUES (currval(pg_get_serial_sequence('orders', 'order_id')),
        1013, 99, 65.00);

-- FAILS: 98 - 99 = -1 violates chk_ticket_types_available_quantity.
--   ERROR:  new row for relation "ticket_types" violates check constraint
--           "chk_ticket_types_available_quantity"
UPDATE ticket_types
SET available_quantity = available_quantity - 99
WHERE ticket_type_id = 1013;

ROLLBACK;

-- Proof: the order and item that had succeeded are gone, and inventory is
-- still 98. All three columns below must read 0, 0, 98.
SELECT
    (SELECT COUNT(*) FROM orders WHERE total_amount = 6435.00) AS ghost_orders,
    (SELECT COUNT(*) FROM order_items WHERE quantity = 99)     AS ghost_items,
    (SELECT available_quantity FROM ticket_types
      WHERE ticket_type_id = 1013)                             AS avail_1013;


-- ============================================================
-- SCENARIO 3 -- the wallet cannot go negative
--   Same shape, different guard: the payment step is what fails.
--   The subtraction is computed from the current balance so the overdraft
--   happens no matter what scenario 1 left behind.
-- ============================================================
BEGIN;

SELECT user_id, wallet_balance
FROM users
WHERE user_id = 402
FOR UPDATE;

INSERT INTO orders (user_id, order_date, status,
                    subtotal, service_fee, tax_amount, total_amount)
VALUES (402, CURRENT_TIMESTAMP, 'pending',
        99999.00, 0.00, 0.00, 99999.00)
RETURNING order_id;

-- FAILS: drives wallet_balance to -1.00, violating users_wallet_balance_check.
UPDATE users
SET wallet_balance = wallet_balance - (wallet_balance + 1.00)
WHERE user_id = 402;

ROLLBACK;

-- Proof: balance untouched, no pending order left behind.
SELECT
    (SELECT wallet_balance FROM users WHERE user_id = 402)      AS wallet,
    (SELECT COUNT(*) FROM orders WHERE status = 'pending')      AS pending,
    (SELECT COUNT(*) FROM orders WHERE total_amount = 99999.00) AS ghost;


-- ============================================================
-- SCENARIO 4 -- the same work as one stored-function call
--   purchase_tickets() in sql/purchase_tickets.sql performs every step from
--   scenario 1 inside a single function body. A function call is already
--   atomic, so a RAISE anywhere inside it undoes everything it had written.
--   This is the path app/services/purchase_service.py actually uses.
-- ============================================================

-- Succeeds: 1 x Workshop Admission, $45.00.
SELECT * FROM purchase_tickets(402, 1012, 1, 'Wallet');

-- Rejected before anything is written.
--   ERROR:  Maximum purchase is 3 ticket(s).
SELECT * FROM purchase_tickets(402, 1013, 50, 'Credit Card');

-- Rejected by the inventory guard. The function tests maximum_purchase
-- before stock, so the request has to stay inside the per-order limit (3)
-- while exceeding what is left. Drain 1013 to 2 to set that up.
UPDATE ticket_types SET available_quantity = 2 WHERE ticket_type_id = 1013;

--   ERROR:  Not enough tickets available.
SELECT * FROM purchase_tickets(402, 1013, 3, 'Credit Card');


-- ============================================================
-- AFTER
--   Only scenario 1 and the successful call in scenario 4 changed anything:
--   3 tickets left 1012 (148 -> 145), $135.00 left the wallet
--   (2500.00 -> 2365.00), and 2 orders were added. Scenarios 2 and 3 left no
--   trace. avail_1013 reads 2 because of the deliberate drain above, not
--   because anything was sold; RESET puts it back to 98.
--
--   Note that the new order_ids are not consecutive. Scenarios 2 and 3 each
--   consumed a sequence value before rolling back, and sequences do not roll
--   back -- by design, since two sessions must never be handed the same id.
-- ============================================================
SELECT
    (SELECT wallet_balance FROM users WHERE user_id = 402) AS wallet,
    (SELECT available_quantity FROM ticket_types
      WHERE ticket_type_id = 1012)                         AS avail_1012,
    (SELECT available_quantity FROM ticket_types
      WHERE ticket_type_id = 1013)                         AS avail_1013,
    (SELECT COUNT(*) FROM orders)                          AS orders,
    (SELECT COUNT(*) FROM order_items)                     AS order_items,
    (SELECT COUNT(*) FROM payments)                        AS payments;


-- ============================================================
-- RESET
--   Returns the database to the post-seed state so the demo can be re-run.
-- ============================================================
-- BEGIN;
-- DELETE FROM payments    WHERE order_id > 5015;
-- DELETE FROM order_items WHERE order_id > 5015;
-- DELETE FROM orders      WHERE order_id > 5015;
-- UPDATE ticket_types SET available_quantity = 148 WHERE ticket_type_id = 1012;
-- UPDATE ticket_types SET available_quantity =  98 WHERE ticket_type_id = 1013;
-- UPDATE users SET wallet_balance = 2500.00 WHERE user_id = 402;
-- COMMIT;
