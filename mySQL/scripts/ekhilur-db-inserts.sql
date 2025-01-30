-- INSERTS FOR USER TABLE
-- 
--
INSERT INTO `ekhilur`.`users` (`user_id`, `name`, `email`, `password`, `two_factor_enabled`, `role`)
VALUES 
(1, 'Saul', 'saulmorahernandez96@gmail.com', '$2a$10$pgQBYbxVUAhEC0EHVIuRcekINTZiYr1Fa9oxvTSCxdKm..SImS9Mq', TRUE, 'admin'),
(2, 'Ekhilur', 'ekhiluradmin@gmail.com', '$2a$10$pgQBYbxVUAhEC0EHVIuRcekINTZiYr1Fa9oxvTSCxdKm..SImS9Mq', TRUE, 'council'),
(3, 'Ekaitz', 'ekaitzguerra@gmail.com', '$2a$10$pgQBYbxVUAhEC0EHVIuRcekINTZiYr1Fa9oxvTSCxdKm..SImS9Mq', TRUE, 'user'),
(4, 'Ekaitzz', 'arashi.eka@gmail.com', '$2a$10$pgQBYbxVUAhEC0EHVIuRcekINTZiYr1Fa9oxvTSCxdKm..SImS9Mq', TRUE, 'user'),
(5, 'Adrian', 'abujanrodriguez@gmail.com', '$2a$10$zuANOpz1cwDK4/eyZuqJMeiED5OmYRYc4up86ooMwahrPK/Hn5DaC', TRUE, 'user');