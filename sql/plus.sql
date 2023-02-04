-- Get plus for a user
SELECT	U.username, P.has_plus
FROM 	account_profile P
JOIN 	account_account A ON A.id = P.account_id
JOIN 	account_user U ON A.user_id = U.id
WHERE 	U.username = '@adamghill@indieweb.social'
;

-- Set plus for a user
UPDATE  account_profile P
SET 	has_plus = True
FROM 	account_account A
JOIN 	account_user U ON A.user_id = U.id
WHERE 	A.id = P.account_id
AND 	U.username = '@adamghill@indieweb.social'
;
