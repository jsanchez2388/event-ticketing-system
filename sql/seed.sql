BEGIN;

-- ============================================================
-- venues
-- ============================================================
INSERT INTO venues (venue_id, venue_name, street, city, state, zip_code,
                    country, capacity, phone, website_url) VALUES
    (1, 'Hollywood Bowl', '2301 Highland Ave',
     'Los Angeles', 'CA', '90068', 'United States', 17500,
     '323-850-2000', 'https://www.hollywoodbowl.com'),
    (2, 'Los Angeles Convention Center', '1201 S Figueroa St',
     'Los Angeles', 'CA', '90015', 'United States', 10000,
     '213-741-1151', 'https://www.lacclink.com'),
    (3, 'Dodger Stadium', '1000 Vin Scully Ave',
     'Los Angeles', 'CA', '90012', 'United States', 56000,
     '866-363-4377', 'https://www.mlb.com/dodgers/ballpark'),
    (4, 'CSUN University Student Union', '18111 Nordhoff St',
     'Northridge', 'CA', '91330', 'United States', 1200,
     '818-677-2251', 'https://www.csun.edu/usu'),
    (5, 'Santa Clarita Community Center', '22421 Market St',
     'Newhall', 'CA', '91321', 'United States', 500,
     '661-259-2489', NULL),
    (6, 'Placerita Canyon Nature Center', '19152 Placerita Canyon Rd',
     'Newhall', 'CA', '91321', 'United States', 300,
     '661-259-7721', 'https://parks.lacounty.gov/placerita-canyon-state-park');

-- ============================================================
-- event_categories
-- ============================================================
INSERT INTO event_categories (category_id, category_name,
                              category_description) VALUES
    (1, 'Music', 'Concerts and live musical performances'),
    (2, 'Technology', 'Technology, computing, data science, and AI events'),
    (3, 'Sports', 'Professional, amateur, and recreational sporting events'),
    (4, 'Education', 'Academic and educational events'),
    (5, 'Community', 'Community gatherings and civic activities'),
    (6, 'Workshop', 'Hands-on instructional and skill-building events'),
    (7, 'Networking', 'Professional and social networking events'),
    (8, 'Outdoors', 'Outdoor recreation, conservation, and nature events');

-- ============================================================
-- users
--   wallet_balance mirrors app/services/auth_service.py: 1000.00 for an
--   administrator, 500.00 for a customer.
--   Each password_hash is a distinct bcrypt digest of the same password;
--   bcrypt salts every call, so identical passwords never share a hash.
-- ============================================================
INSERT INTO users (user_id, first_name, last_name, email, phone,
                   password_hash, account_status, role, wallet_balance,
                   created_at, updated_at) VALUES
    (401, 'Maya', 'Lopez', 'maya.lopez@example.com', '818-555-0101',
     '$2b$12$BINeKG9n1vKPH1iKzr50aevFJOLbTNkENsWQin4g7pi7zBYNxeMbi',
     'active', 'admin', 1000.00, '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (402, 'Jordan', 'Kim', 'jordan.kim@example.com', '818-555-0102',
     '$2b$12$i40vbiDzag0ywx6G/QkV2.Vk4SiHgK5PMWXzqOC0hubazyqaabL1G',
     'active', 'user', 2500.00, '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (403, 'Avery', 'Patel', 'avery.patel@example.com', '818-555-0103',
     '$2b$12$JdJEXtajhx9Et13copCF..Sbqg5TVvoVpRyEwW3IYPErHZArMnuiC',
     'active', 'user', 500.00, '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (404, 'Noah', 'Garcia', 'noah.garcia@example.com', '818-555-0104',
     '$2b$12$PKdncvNc3zwnwH6pXkPgpOGt9NGK1o1.yH5TR.WPJXySL/cdFb43u',
     'active', 'user', 500.00, '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (405, 'Emma', 'Nguyen', 'emma.nguyen@example.com', '818-555-0105',
     '$2b$12$R/ODNh3Vka1v2Hgf/4zXx.jkwGa.B7.sZVWKxp8bcTxM2sb/j/7XK',
     'active', 'user', 500.00, '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00');

-- ============================================================
-- events
-- ============================================================
INSERT INTO events (event_id, venue_id, title, event_type, start_datetime,
                    end_datetime, status, created_at, updated_at) VALUES
    (101, 1, 'Bruno Mars', 'Concert',
     '2026-11-16 03:00:00+00', '2026-11-16 06:30:00+00', 'scheduled', '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (102, 2, 'West Coast Data Science & AI Summit', 'Conference',
     '2026-10-22 15:30:00+00', '2026-10-23 00:30:00+00', 'scheduled', '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (103, 3, 'Los Angeles Dodgers vs. San Diego Padres', 'Sport',
     '2026-09-27 23:10:00+00', '2026-09-28 02:30:00+00', 'scheduled', '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (104, 4, 'CSUN Master of Science in Data Science Mixer', 'University Event',
     '2026-10-09 00:00:00+00', '2026-10-09 03:00:00+00', 'scheduled', '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (105, 5, 'Urban Container Gardening & Propagation', 'Workshop',
     '2026-10-17 17:00:00+00', '2026-10-17 20:00:00+00', 'scheduled', '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00'),
    (106, 6, 'Trail Cleanup & Hike', 'Community Event',
     '2026-10-24 15:00:00+00', '2026-10-24 20:00:00+00', 'scheduled', '2026-06-01 12:00:00+00', '2026-06-01 12:00:00+00');

-- ============================================================
-- event_category_map
--   102, 104 and 105 sit in several categories, which is the
--   many-to-many case; 101, 103 and 106 show the simple one.
-- ============================================================
INSERT INTO event_category_map (event_id, category_id) VALUES
    (101, 1),
    (102, 2),
    (102, 4),
    (102, 7),
    (103, 3),
    (104, 4),
    (104, 7),
    (105, 4),
    (105, 5),
    (105, 6),
    (106, 5),
    (106, 8);

-- ============================================================
-- ticket_types
--   available_quantity = total_quantity - (quantity sold in order_items)
-- ============================================================
INSERT INTO ticket_types (ticket_type_id, event_id, ticket_name, price,
                          total_quantity, available_quantity,
                          minimum_purchase, maximum_purchase,
                          sales_start, sales_end, status) VALUES
    -- event 101, sold 5 of 8000
    (1001, 101, 'General Admission', 199.00, 8000, 7995, 1, 8,
     '2026-07-01 16:00:00+00', '2026-11-16 02:00:00+00', 'active'),
    -- event 101, sold 2 of 1000
    (1002, 101, 'VIP', 275.00, 1000, 998, 1, 4,
     '2026-07-01 16:00:00+00', '2026-11-16 02:00:00+00', 'active'),
    -- event 101, sold 3 of 2500
    (1003, 101, 'Floor', 195.00, 2500, 2497, 1, 6,
     '2026-07-01 16:00:00+00', '2026-11-16 02:00:00+00', 'active'),
    -- event 102, sold 3 of 2500
    (1004, 102, 'General Conference Pass', 149.00, 2500, 2497, 1, 6,
     '2026-06-15 16:00:00+00', '2026-10-22 14:30:00+00', 'active'),
    -- event 102, sold 3 of 1000
    (1005, 102, 'Student Pass', 69.00, 1000, 997, 1, 4,
     '2026-06-15 16:00:00+00', '2026-10-22 14:30:00+00', 'active'),
    -- event 102, sold 2 of 300
    (1006, 102, 'VIP Conference Pass', 299.00, 300, 298, 1, 2,
     '2026-06-15 16:00:00+00', '2026-10-22 14:30:00+00', 'active'),
    -- event 103, sold 4 of 15000
    (1007, 103, 'Reserve Level', 55.00, 15000, 14996, 1, 8,
     '2026-06-20 16:00:00+00', '2026-09-27 22:00:00+00', 'active'),
    -- event 103, sold 3 of 10000
    (1008, 103, 'Field Level', 140.00, 10000, 9997, 1, 8,
     '2026-06-20 16:00:00+00', '2026-09-27 22:00:00+00', 'active'),
    -- event 103, sold 3 of 3500
    (1009, 103, 'Club Level', 220.00, 3500, 3497, 1, 6,
     '2026-06-20 16:00:00+00', '2026-09-27 22:00:00+00', 'active'),
    -- event 104, sold 4 of 500
    (1010, 104, 'Student', 10.00, 500, 496, 1, 4,
     '2026-08-01 16:00:00+00', '2026-10-08 23:00:00+00', 'active'),
    -- event 104, sold 2 of 300
    (1011, 104, 'Alumni / Guest', 20.00, 300, 298, 1, 4,
     '2026-08-01 16:00:00+00', '2026-10-08 23:00:00+00', 'active'),
    -- event 105, sold 2 of 150
    (1012, 105, 'Workshop Admission', 45.00, 150, 148, 1, 4,
     '2026-08-15 16:00:00+00', '2026-10-17 16:00:00+00', 'active'),
    -- event 105, sold 2 of 100
    (1013, 105, 'Workshop + Materials Kit', 65.00, 100, 98, 1, 3,
     '2026-08-15 16:00:00+00', '2026-10-17 16:00:00+00', 'active'),
    -- event 106, sold 4 of 200
    (1014, 106, 'Volunteer Registration', 0.00, 200, 196, 1, 6,
     '2026-08-20 16:00:00+00', '2026-10-24 14:00:00+00', 'active'),
    -- event 106, sold 3 of 100
    (1015, 106, 'Supporter Donation Ticket', 15.00, 100, 97, 1, 5,
     '2026-08-20 16:00:00+00', '2026-10-24 14:00:00+00', 'active');

-- ============================================================
-- orders
--   service_fee and tax_amount are 0.00, matching purchase_tickets() in
--   sql/purchase_tickets.sql, so total_amount equals subtotal.
-- ============================================================
INSERT INTO orders (order_id, user_id, order_date, status, subtotal,
                    service_fee, tax_amount, total_amount) VALUES
    (5001, 403, '2026-06-18 19:30:00+00',
     'completed', 298.00, 0.00, 0.00, 298.00),
    (5002, 402, '2026-06-25 21:05:00+00',
     'completed', 360.00, 0.00, 0.00, 360.00),
    (5003, 404, '2026-07-03 18:40:00+00',
     'completed', 398.00, 0.00, 0.00, 398.00),
    (5004, 402, '2026-07-14 22:15:00+00',
     'completed', 940.00, 0.00, 0.00, 940.00),
    (5005, 403, '2026-07-28 17:20:00+00',
     'completed', 660.00, 0.00, 0.00, 660.00),
    (5006, 403, '2026-08-05 20:00:00+00',
     'completed', 736.00, 0.00, 0.00, 736.00),
    (5007, 402, '2026-08-19 16:45:00+00',
     'completed', 80.00, 0.00, 0.00, 80.00),
    (5008, 405, '2026-08-27 23:30:00+00',
     'completed', 90.00, 0.00, 0.00, 90.00),
    (5009, 402, '2026-09-02 19:10:00+00',
     'completed', 597.00, 0.00, 0.00, 597.00),
    (5010, 404, '2026-09-11 21:50:00+00',
     'completed', 280.00, 0.00, 0.00, 280.00),
    (5011, 403, '2026-09-19 18:05:00+00',
     'completed', 0.00, 0.00, 0.00, 0.00),
    (5012, 404, '2026-09-30 20:25:00+00',
     'completed', 45.00, 0.00, 0.00, 45.00),
    (5013, 405, '2026-10-02 17:35:00+00',
     'completed', 218.00, 0.00, 0.00, 218.00),
    (5014, 404, '2026-10-05 22:40:00+00',
     'completed', 130.00, 0.00, 0.00, 130.00),
    (5015, 405, '2026-10-06 19:55:00+00',
     'completed', 195.00, 0.00, 0.00, 195.00);

-- ============================================================
-- order_items
-- ============================================================
INSERT INTO order_items (order_item_id, order_id, ticket_type_id,
                         quantity, unit_price) VALUES
    (6001, 5001, 1004, 2, 149.00),
    (6002, 5002, 1007, 4, 55.00),
    (6003, 5002, 1008, 1, 140.00),
    (6004, 5003, 1001, 2, 199.00),
    (6005, 5004, 1002, 2, 275.00),
    (6006, 5004, 1003, 2, 195.00),
    (6007, 5005, 1009, 3, 220.00),
    (6008, 5006, 1006, 2, 299.00),
    (6009, 5006, 1005, 2, 69.00),
    (6010, 5007, 1010, 4, 10.00),
    (6011, 5007, 1011, 2, 20.00),
    (6012, 5008, 1012, 2, 45.00),
    (6013, 5009, 1001, 3, 199.00),
    (6014, 5010, 1008, 2, 140.00),
    (6015, 5011, 1014, 4, 0.00),
    (6016, 5012, 1015, 3, 15.00),
    (6017, 5013, 1004, 1, 149.00),
    (6018, 5013, 1005, 1, 69.00),
    (6019, 5014, 1013, 2, 65.00),
    (6020, 5015, 1003, 1, 195.00);

-- ============================================================
-- payments
--   One completed payment per order. transaction_reference is the
--   idempotency key, so every value here is distinct.
-- ============================================================
INSERT INTO payments (payment_id, order_id, amount, payment_method,
                      payment_status, transaction_reference,
                      payment_date) VALUES
    (7001, 5001, 298.00, 'Credit Card', 'completed', 'TXN-SEED-5001', '2026-06-18 19:30:00+00'),
    (7002, 5002, 360.00, 'Credit Card', 'completed', 'TXN-SEED-5002', '2026-06-25 21:05:00+00'),
    (7003, 5003, 398.00, 'PayPal', 'completed', 'TXN-SEED-5003', '2026-07-03 18:40:00+00'),
    (7004, 5004, 940.00, 'Credit Card', 'completed', 'TXN-SEED-5004', '2026-07-14 22:15:00+00'),
    (7005, 5005, 660.00, 'Apple Pay', 'completed', 'TXN-SEED-5005', '2026-07-28 17:20:00+00'),
    (7006, 5006, 736.00, 'Credit Card', 'completed', 'TXN-SEED-5006', '2026-08-05 20:00:00+00'),
    (7007, 5007, 80.00, 'Wallet', 'completed', 'TXN-SEED-5007', '2026-08-19 16:45:00+00'),
    (7008, 5008, 90.00, 'Google Pay', 'completed', 'TXN-SEED-5008', '2026-08-27 23:30:00+00'),
    (7009, 5009, 597.00, 'Credit Card', 'completed', 'TXN-SEED-5009', '2026-09-02 19:10:00+00'),
    (7010, 5010, 280.00, 'PayPal', 'completed', 'TXN-SEED-5010', '2026-09-11 21:50:00+00'),
    (7011, 5011, 0.00, 'No Charge', 'completed', 'TXN-SEED-5011', '2026-09-19 18:05:00+00'),
    (7012, 5012, 45.00, 'Wallet', 'completed', 'TXN-SEED-5012', '2026-09-30 20:25:00+00'),
    (7013, 5013, 218.00, 'Credit Card', 'completed', 'TXN-SEED-5013', '2026-10-02 17:35:00+00'),
    (7014, 5014, 130.00, 'Apple Pay', 'completed', 'TXN-SEED-5014', '2026-10-05 22:40:00+00'),
    (7015, 5015, 195.00, 'Wallet', 'completed', 'TXN-SEED-5015', '2026-10-06 19:55:00+00');

-- ============================================================
-- identity sequences
--   Every id above was supplied explicitly, which leaves the identity
--   sequences at 1. Without this block the first INSERT from the API
--   would try user_id 1 and collide. pg_get_serial_sequence() resolves
--   the sequence behind each identity column.
-- ============================================================
SELECT setval(pg_get_serial_sequence('users', 'user_id'),
              COALESCE((SELECT MAX(user_id) FROM users), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('venues', 'venue_id'),
              COALESCE((SELECT MAX(venue_id) FROM venues), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('event_categories', 'category_id'),
              COALESCE((SELECT MAX(category_id) FROM event_categories), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('events', 'event_id'),
              COALESCE((SELECT MAX(event_id) FROM events), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('ticket_types', 'ticket_type_id'),
              COALESCE((SELECT MAX(ticket_type_id) FROM ticket_types), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('orders', 'order_id'),
              COALESCE((SELECT MAX(order_id) FROM orders), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('order_items', 'order_item_id'),
              COALESCE((SELECT MAX(order_item_id) FROM order_items), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('payments', 'payment_id'),
              COALESCE((SELECT MAX(payment_id) FROM payments), 0) + 1, false);

COMMIT;

-- ============================================================
-- load check
-- ============================================================
--   venues 6 | event_categories 8 | users 5 | events 6
--   event_category_map 12 | ticket_types 15 | orders 15
--   order_items 20 | payments 15
--   tickets sold 45 | gross revenue $5027.00

SELECT
    (SELECT COUNT(*) FROM venues)             AS venues,
    (SELECT COUNT(*) FROM event_categories)   AS categories,
    (SELECT COUNT(*) FROM users)              AS users,
    (SELECT COUNT(*) FROM events)             AS events,
    (SELECT COUNT(*) FROM event_category_map) AS category_map,
    (SELECT COUNT(*) FROM ticket_types)       AS ticket_types,
    (SELECT COUNT(*) FROM orders)             AS orders,
    (SELECT COUNT(*) FROM order_items)        AS order_items,
    (SELECT COUNT(*) FROM payments)           AS payments;
