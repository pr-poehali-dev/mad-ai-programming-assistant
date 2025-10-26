-- Создаем таблицу для игр
CREATE TABLE IF NOT EXISTS games_database (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    developer VARCHAR(500),
    publisher VARCHAR(500),
    release_year INTEGER,
    genre VARCHAR(200),
    platform VARCHAR(500),
    description TEXT,
    keywords TEXT[]
);

-- Создаем таблицу для артистов/знаменитостей
CREATE TABLE IF NOT EXISTS celebrities_database (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    profession VARCHAR(200),
    birth_year INTEGER,
    nationality VARCHAR(200),
    known_for TEXT,
    description TEXT,
    keywords TEXT[]
);

-- Добавляем популярные игры
INSERT INTO games_database (name, developer, publisher, release_year, genre, platform, description, keywords) VALUES
('Minecraft', 'Mojang Studios', 'Mojang Studios', 2011, 'Sandbox, Survival', 'PC, консоли, мобильные', 'Культовая игра-песочница с блочной графикой, где можно строить и исследовать бесконечные миры', ARRAY['minecraft', 'майнкрафт', 'блоки', 'песочница']),
('Roblox', 'Roblox Corporation', 'Roblox Corporation', 2006, 'Платформа для игр', 'PC, консоли, мобильные', 'Онлайн-платформа для создания и игры в пользовательские игры', ARRAY['roblox', 'роблокс']),
('GTA 5', 'Rockstar North', 'Rockstar Games', 2013, 'Action, Open World', 'PC, PlayStation, Xbox', 'Культовый экшен с открытым миром в Лос-Сантосе', ARRAY['gta', 'гта', 'grand theft auto', 'лос-сантос']),
('The Witcher 3', 'CD Projekt Red', 'CD Projekt', 2015, 'RPG, Action', 'PC, PlayStation, Xbox', 'Эпическая RPG про Геральта из Ривии', ARRAY['witcher', 'ведьмак', 'геральт', 'цири']),
('CS:GO', 'Valve', 'Valve', 2012, 'Shooter, Tactical', 'PC', 'Легендарный тактический шутер 5 на 5', ARRAY['csgo', 'counter strike', 'кс го', 'шутер']),
('Fortnite', 'Epic Games', 'Epic Games', 2017, 'Battle Royale', 'PC, консоли, мобильные', 'Популярная королевская битва с уникальным строительством', ARRAY['fortnite', 'фортнайт', 'батл рояль']),
('Dota 2', 'Valve', 'Valve', 2013, 'MOBA', 'PC', 'Культовая MOBA с международными турнирами', ARRAY['dota', 'дота', 'мoba']),
('League of Legends', 'Riot Games', 'Riot Games', 2009, 'MOBA', 'PC', 'Самая популярная MOBA в мире', ARRAY['lol', 'league', 'лига легенд', 'лол']),
('Valorant', 'Riot Games', 'Riot Games', 2020, 'Tactical Shooter', 'PC', 'Тактический шутер с уникальными способностями агентов', ARRAY['valorant', 'валорант']),
('Among Us', 'Innersloth', 'Innersloth', 2018, 'Party, Social Deduction', 'PC, мобильные', 'Социальная игра про предателей в космосе', ARRAY['among us', 'амонг ас', 'импостор']);

-- Добавляем популярных артистов
INSERT INTO celebrities_database (name, profession, birth_year, nationality, known_for, description, keywords) VALUES
('Моргенштерн', 'Рэпер, продюсер', 1998, 'Россия/Беларусь', 'Рэп, скандальные треки', 'Один из самых популярных русскоязычных рэперов, известен провокационным стилем', ARRAY['моргенштерн', 'morgenshtern', 'рэпер']),
('Егор Крид', 'Певец, рэпер', 1994, 'Россия', 'Поп-рэп, хиты "Самая самая"', 'Популярный российский исполнитель, экс-участник Black Star', ARRAY['егор крид', 'egor kreed', 'крид']),
('Billie Eilish', 'Певица', 2001, 'США', 'Альтернативный поп, Grammy', 'Американская певица, обладательница множества Grammy', ARRAY['billie', 'билли айлиш', 'eilish']),
('The Weeknd', 'Певец', 1990, 'Канада', 'R&B, поп, "Blinding Lights"', 'Канадский певец, один из самых прослушиваемых артистов', ARRAY['weeknd', 'уикенд', 'абель']),
('Drake', 'Рэпер, певец', 1986, 'Канада', 'Хип-хоп, R&B', 'Один из самых успешных рэперов всех времён', ARRAY['drake', 'дрейк']),
('Тимати', 'Рэпер, продюсер', 1983, 'Россия', 'Black Star, бизнес', 'Основатель лейбла Black Star, предприниматель', ARRAY['тимати', 'timati', 'black star']),
('Oxxxymiron', 'Рэпер', 1985, 'Россия/Великобритания', 'Рэп-баттлы, интеллектуальный рэп', 'Один из самых влиятельных русскоязычных рэперов', ARRAY['оксимирон', 'oxxxymiron', 'окси']),
('Скриптонит', 'Рэпер', 1990, 'Казахстан', 'Казахстанский рэп, Musica36', 'Популярный казахстанский рэпер, основатель Musica36', ARRAY['скриптонит', 'scriptonite', 'скрип']),
('Pharaoh', 'Рэпер', 1996, 'Россия', 'Клауд-рэп, Dead Dynasty', 'Российский рэпер, пионер клауд-рэпа в России', ARRAY['pharaoh', 'фараон', 'dead dynasty']),
('Элджей', 'Рэпер, певец', 1993, 'Россия', 'Трэп, "Розовое вино"', 'Популярный российский исполнитель в жанре трэп', ARRAY['элджей', 'eldjey', 'eldzhey']);

CREATE INDEX idx_games_keywords ON games_database USING GIN(keywords);
CREATE INDEX idx_celebrities_keywords ON celebrities_database USING GIN(keywords);
