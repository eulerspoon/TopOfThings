CREATE TRIGGER IF NOT EXISTS update_positions
AFTER INSERT ON things_in_tops
FOR EACH ROW
BEGIN
    UPDATE things_in_tops
    SET position = position + 1
    WHERE chat_id = NEW.chat_id
        AND position >= NEW.position
        AND (thing_id != NEW.thing_id);
END;