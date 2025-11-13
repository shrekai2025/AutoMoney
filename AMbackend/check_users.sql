-- Check all users and their active status
SELECT 
    id,
    email,
    google_id as firebase_uid,
    full_name,
    role,
    is_active,
    is_superuser,
    created_at
FROM "user"
ORDER BY created_at DESC;

-- Count of active vs inactive users
SELECT 
    is_active,
    COUNT(*) as count
FROM "user"
GROUP BY is_active;

