CREATE OR REPLACE FUNCTION public.purchase_tickets(p_user_id bigint, p_ticket_type_id bigint, p_quantity integer, p_payment_method character varying)
 RETURNS TABLE(new_order_id bigint, event_id bigint, purchased_ticket_type_id bigint, quantity_purchased integer, unit_price numeric, order_total numeric, remaining_inventory integer, remaining_balance numeric)
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_event_id BIGINT;
    v_price NUMERIC(10,2);

    v_available_quantity INTEGER;
    v_minimum_purchase INTEGER;
    v_maximum_purchase INTEGER;

    v_wallet_balance NUMERIC(12,2);

    v_subtotal NUMERIC(10,2);
    v_service_fee NUMERIC(10,2);
    v_tax_amount NUMERIC(10,2);
    v_total_amount NUMERIC(10,2);

    v_order_id BIGINT;

    v_remaining_inventory INTEGER;
    v_remaining_balance NUMERIC(12,2);

    v_transaction_reference VARCHAR(255);

BEGIN

    IF p_quantity <= 0 THEN
        RAISE EXCEPTION
            'Purchase quantity must be greater than zero.';
    END IF;


    -- Lock the user's wallet
    SELECT
        u.wallet_balance

    INTO
        v_wallet_balance

    FROM users AS u

    WHERE u.user_id = p_user_id

    FOR UPDATE;


    IF NOT FOUND THEN
        RAISE EXCEPTION
            'User % does not exist.',
            p_user_id;
    END IF;


    -- Lock ticket inventory
    SELECT
        tt.event_id,
        tt.price,
        tt.available_quantity,
        tt.minimum_purchase,
        tt.maximum_purchase

    INTO
        v_event_id,
        v_price,
        v_available_quantity,
        v_minimum_purchase,
        v_maximum_purchase

    FROM ticket_types AS tt

    WHERE tt.ticket_type_id = p_ticket_type_id

    FOR UPDATE;


    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Ticket type % does not exist.',
            p_ticket_type_id;
    END IF;


    IF p_quantity < v_minimum_purchase THEN
        RAISE EXCEPTION
            'Minimum purchase is % ticket(s).',
            v_minimum_purchase;
    END IF;


    IF p_quantity > v_maximum_purchase THEN
        RAISE EXCEPTION
            'Maximum purchase is % ticket(s).',
            v_maximum_purchase;
    END IF;


    IF v_available_quantity < p_quantity THEN
        RAISE EXCEPTION
            'Not enough tickets available.';
    END IF;


    v_subtotal :=
        ROUND(v_price * p_quantity, 2);

    v_service_fee := 0.00;
    v_tax_amount := 0.00;

    v_total_amount :=
        v_subtotal
        + v_service_fee
        + v_tax_amount;


    -- Make sure the user can afford it
    IF v_wallet_balance < v_total_amount THEN

        RAISE EXCEPTION
            'Insufficient balance. Balance: $%, Purchase: $%',
            v_wallet_balance,
            v_total_amount;

    END IF;


    -- Create order
    INSERT INTO orders (
        user_id,
        order_date,
        status,
        subtotal,
        service_fee,
        tax_amount,
        total_amount
    )

    VALUES (
        p_user_id,
        CURRENT_TIMESTAMP,
        'completed',
        v_subtotal,
        v_service_fee,
        v_tax_amount,
        v_total_amount
    )

    RETURNING orders.order_id
    INTO v_order_id;


    -- Create order item
    INSERT INTO order_items (
        order_id,
        ticket_type_id,
        quantity,
        unit_price
    )

    VALUES (
        v_order_id,
        p_ticket_type_id,
        p_quantity,
        v_price
    );


    -- Reduce ticket inventory
    UPDATE ticket_types AS tt

    SET available_quantity =
        tt.available_quantity - p_quantity

    WHERE tt.ticket_type_id =
        p_ticket_type_id

    RETURNING tt.available_quantity
    INTO v_remaining_inventory;


    -- Remove money from wallet
    UPDATE users AS u

    SET wallet_balance =
        u.wallet_balance - v_total_amount

    WHERE u.user_id =
        p_user_id

    RETURNING u.wallet_balance
    INTO v_remaining_balance;


    -- Payment reference
    v_transaction_reference :=
        'TXN-'
        || v_order_id
        || '-'
        || TO_CHAR(
            clock_timestamp(),
            'YYYYMMDDHH24MISSMS'
        );


    -- Payment record
    INSERT INTO payments (
        order_id,
        amount,
        payment_method,
        payment_status,
        transaction_reference,
        payment_date
    )

    VALUES (
        v_order_id,
        v_total_amount,
        p_payment_method,
        'completed',
        v_transaction_reference,
        CURRENT_TIMESTAMP
    );


    RETURN QUERY

    SELECT
        v_order_id,
        v_event_id,
        p_ticket_type_id,
        p_quantity,
        v_price,
        v_total_amount,
        v_remaining_inventory,
        v_remaining_balance;

END;
$function$

