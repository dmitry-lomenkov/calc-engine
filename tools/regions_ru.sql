DROP TABLE IF EXISTS geo.admin1_ru;
CREATE TABLE geo.admin1_ru(en_name text PRIMARY KEY, ru_name text);
INSERT INTO geo.admin1_ru(en_name, ru_name) VALUES
('Adygeya Republic','Республика Адыгея'),('Altai','Республика Алтай'),('Altai Krai','Алтайский край'),
('Amur Oblast','Амурская область'),('Arkhangelskaya','Архангельская область'),('Astrakhan Oblast','Астраханская область'),
('Bashkortostan Republic','Республика Башкортостан'),('Belgorod Oblast','Белгородская область'),('Bryansk Oblast','Брянская область'),
('Buryatiya Republic','Республика Бурятия'),('Chechnya','Чеченская Республика'),('Chelyabinsk','Челябинская область'),
('Chukotka','Чукотский АО'),('Chuvash Republic','Чувашская Республика'),('Dagestan','Республика Дагестан'),
('Ingushetiya Republic','Республика Ингушетия'),('Irkutsk Oblast','Иркутская область'),('Ivanovo Oblast','Ивановская область'),
('Kabardino-Balkariya Republic','Кабардино-Балкарская Республика'),('Kaliningrad Oblast','Калининградская область'),
('Kalmykiya Republic','Республика Калмыкия'),('Kaluga Oblast','Калужская область'),
('Karachayevo-Cherkesiya Republic','Карачаево-Черкесская Республика'),('Karelia','Республика Карелия'),
('Kuzbass','Кемеровская область'),('Khabarovsk','Хабаровский край'),('Khakasiya Republic','Республика Хакасия'),
('Khanty-Mansia','Ханты-Мансийский АО'),('Kirov Oblast','Кировская область'),('Komi','Республика Коми'),
('Kostroma Oblast','Костромская область'),('Krasnodar Krai','Краснодарский край'),('Kurgan Oblast','Курганская область'),
('Kursk Oblast','Курская область'),('Leningradskaya Oblast''','Ленинградская область'),('Lipetsk Oblast','Липецкая область'),
('Magadan Oblast','Магаданская область'),('Mariy-El Republic','Республика Марий Эл'),('Mordoviya Republic','Республика Мордовия'),
('Moscow Oblast','Московская область'),('Moscow','Москва'),('Murmansk','Мурманская область'),('Nenets','Ненецкий АО'),
('Nizhny Novgorod Oblast','Нижегородская область'),('Novgorod Oblast','Новгородская область'),('Novosibirsk Oblast','Новосибирская область'),
('Omsk Oblast','Омская область'),('Orenburg Oblast','Оренбургская область'),('Oryol oblast','Орловская область'),
('Penza Oblast','Пензенская область'),('Primorye','Приморский край'),('Pskov Oblast','Псковская область'),
('Rostov','Ростовская область'),('Ryazan Oblast','Рязанская область'),('Sakha','Республика Саха (Якутия)'),
('Sakhalin Oblast','Сахалинская область'),('Samara Oblast','Самарская область'),('St.-Petersburg','Санкт-Петербург'),
('Saratov Oblast','Саратовская область'),('North Ossetia–Alania','Республика Северная Осетия — Алания'),
('Smolensk Oblast','Смоленская область'),('Stavropol Kray','Ставропольский край'),('Sverdlovsk Oblast','Свердловская область'),
('Tambov Oblast','Тамбовская область'),('Tatarstan Republic','Республика Татарстан'),('Tomsk Oblast','Томская область'),
('Tula Oblast','Тульская область'),('Tver Oblast','Тверская область'),('Tyumen Oblast','Тюменская область'),
('Republic of Tyva','Республика Тыва'),('Udmurtiya Republic','Удмуртская Республика'),('Ulyanovsk','Ульяновская область'),
('Vladimir Oblast','Владимирская область'),('Volgograd Oblast','Волгоградская область'),('Vologda Oblast','Вологодская область'),
('Voronezh Oblast','Воронежская область'),('Yamalo-Nenets','Ямало-Ненецкий АО'),('Yaroslavl Oblast','Ярославская область'),
('Jewish Autonomous Oblast','Еврейская АО'),('Perm Krai','Пермский край'),('Krasnoyarsk Krai','Красноярский край'),
('Kamchatka','Камчатский край'),('Zabaykalskiy (Transbaikal) Kray','Забайкальский край');

ALTER TABLE geo.places ADD COLUMN IF NOT EXISTS region_ru text;
UPDATE geo.places p SET region_ru = r.ru_name FROM geo.admin1_ru r WHERE p.region = r.en_name;
