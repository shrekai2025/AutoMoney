-- Activate all users
UPDATE "user"
SET is_active = true
WHERE is_active = false;

-- Verify the update
SELECT 
    id,
    email,
    is_active,
    'User activated' as status
FROM "user";

