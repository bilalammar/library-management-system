BEGIN TRANSACTION;
DROP TABLE IF EXISTS books;
CREATE TABLE books (
    book_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT NOT NULL UNIQUE,
    quantity INTEGER NOT NULL,
    amount_of_times_rented INTEGER NOT NULL
);
INSERT INTO "books" VALUES('book_f3a9b1c8', 'The Quantum Paradox', 'Dr. Evelyn Reed', '978-0-345-80378-9', 5, 88);
INSERT INTO "books" VALUES('book_d7e2f6a5', 'Whispers of Eldoria', 'Gideon Ashworth', '978-1-476-71651-9', 3, 124);
INSERT INTO "books" VALUES('book_b4c8d9e1', 'The Last Alchemist', 'Silas Blackwood', '978-0-765-37667-1', 7, 45);
INSERT INTO "books" VALUES('book_a1e5f2b8', 'Galactic Odyssey', 'Aria Vance', '978-0-553-38095-8', 4, 95);
INSERT INTO "books" VALUES('book_c9d3e7f4', 'The Crimson Cipher', 'Julien Croft', '978-0-451-22423-2', 6, 72);
INSERT INTO "books" VALUES('book_e2f6a5b8', 'Echoes of the Void', 'Kaelen Rourke', '978-0-316-05543-3', 2, 151);
INSERT INTO "books" VALUES('book_f1b4c8d9', 'Beneath a Sapphire Sky', 'Lila Summers', '978-0-143-12417-7', 8, 32);
INSERT INTO "books" VALUES('book_a8e2f6b5', 'The Serpent''s Kiss', 'Isolde Verne', '978-0-525-95493-9', 5, 99);
INSERT INTO "books" VALUES('book_c3d7e1f4', 'Chronicles of the Sunstone', 'Valerius magna', '978-1-594-63328-8', 4, 110);
INSERT INTO "books" VALUES('book_b9a5c8d2', 'The Gilded Cage', 'Helena Faye', '978-0-062-39040-3', 7, 65);
INSERT INTO "books" VALUES('book_e6f1b4c8', 'Midnight in the Misted City', 'Inspector Graves', '978-0-385-53797-9', 6, 81);
INSERT INTO "books" VALUES('book_d2a8e5f1', 'The Silicon Soul', 'Unit 734', '978-0-812-55070-2', 9, 130);
INSERT INTO "books" VALUES('book_f4b9c3d7', 'A Taste of Starlight', 'Chef Antoine', '978-1-607-74730-8', 10, 25);
INSERT INTO "books" VALUES('book_c8d2a5e6', 'The Last Voyage of the Orion', 'Captain Eva Rostova', '978-0-441-01359-3', 3, 142);
INSERT INTO "books" VALUES('book_b5a1e9f4', 'The Art of Silent Communication', 'Master Elara', '978-1-577-31901-4', 5, 55);
INSERT INTO "books" VALUES('book_a9e6f1b8', 'Dragon''s Breath Peak', 'Kenji Tanaka', '978-4-088-79811-1', 4, 115);
INSERT INTO "books" VALUES('book_d3c7b2a5', 'The Architect of Dreams', 'Morpheus', '978-0-679-73238-3', 6, 89);
INSERT INTO "books" VALUES('book_f8b4c1d9', 'Shadows Over Ironport', 'Darian Vale', '978-0-765-32636-2', 7, 78);
INSERT INTO "books" VALUES('book_e1a9e6f2', 'The Philosopher''s Paradox', 'Soren', '978-0-199-57354-9', 8, 42);
INSERT INTO "books" VALUES('book_c2d8a5b1', 'Hymn of the Deep', 'Coralia', '978-0-345-53105-2', 5, 93);
INSERT INTO "books" VALUES('book_b1a5c9e6', 'The Clockwork Heart', 'Alister Finch', '978-0-765-38169-9', 4, 101);
INSERT INTO "books" VALUES('book_d7f2b8a1', 'A Study in Emerald', 'Professor Adler', '978-1-408-84618-9', 6, 87);
INSERT INTO "books" VALUES('book_e9f1b4c3', 'The Last Spell', 'Merlin Ambrose', '978-0-451-47432-8', 2, 134);
INSERT INTO "books" VALUES('book_a5c8d2b9', 'Rogue Signal', 'Jax', '978-0-553-58732-2', 7, 105);
INSERT INTO "books" VALUES('book_c6d3e7f1', 'The Cartographer''s Enigma', 'Ptolemy Vance', '978-1-426-21358-8', 5, 68);
INSERT INTO "books" VALUES('book_b8a1e5f2', 'Whispers in the Code', 'Lexi', '978-0-399-59051-5', 8, 118);
INSERT INTO "books" VALUES('book_d1c7b9a5', 'The Sunken Kingdom', 'Admiral Kai', '978-0-765-37656-5', 4, 91);
INSERT INTO "books" VALUES('book_f2b8c4d6', 'The Starlight Thief', 'Nyx', '978-0-062-67840-2', 6, 122);
INSERT INTO "books" VALUES('book_a1e9f4b5', 'The Theory of Everything and Nothing', 'Dr. Lena Petrova', '978-0-307-27829-1', 9, 38);
INSERT INTO "books" VALUES('book_c9d2a8e1', 'The Forgotten Legion', 'General Maximus', '978-0-345-51152-8', 3, 128);
INSERT INTO "books" VALUES('book_b4a5c8d9', 'Echoes from a Distant Star', 'Seraphina', '978-0-316-22258-3', 5, 148);
INSERT INTO "books" VALUES('book_e7f1b9c3', 'The Gryphon''s Gambit', 'Sir Kael', '978-0-765-39145-2', 4, 96);
INSERT INTO "books" VALUES('book_d8c2a1e5', 'The City of Brass and Shadow', 'Nadia al-Fayeed', '978-0-062-67853-2', 6, 108);
INSERT INTO "books" VALUES('book_f1b8c4d2', 'The Way of the Ronin', 'Musashi', '978-4-770-03048-9', 7, 85);
INSERT INTO "books" VALUES('book_a5e9f1b4', 'The Infinite Garden', 'Persephone', '978-0-143-11158-0', 8, 48);
INSERT INTO "books" VALUES('book_c3d7b9a1', 'The Quantum Thief', 'Jean le Flambeur', '978-0-765-36224-7', 5, 138);
INSERT INTO "books" VALUES('book_b9a1e5c8', 'The Last Question', 'Multivac', '978-0-385-48131-4', 10, 155);
INSERT INTO "books" VALUES('book_d2a8c6b4', 'The Amber Spyglass', 'Lyra Belacqua', '978-0-440-22860-2', 3, 140);
INSERT INTO "books" VALUES('book_e6f2b8a1', 'The Martian', 'Mark Watney', '978-0-804-13902-1', 7, 135);
INSERT INTO "books" VALUES('book_f4b5c8d9', 'Project Hail Mary', 'Ryland Grace', '978-0-593-13520-4', 6, 145);
INSERT INTO "books" VALUES('book_c8d1e5f2', 'Ancillary Justice', 'Breq', '978-0-316-24662-6', 4, 120);
INSERT INTO "books" VALUES('book_b1a9e6f4', 'The Three-Body Problem', 'Ye Wenjie', '978-0-765-38203-0', 5, 150);
INSERT INTO "books" VALUES('book_a5c377b9', 'Dune', 'Paul Atreides', '978-0-441-21359-3', 8, 160);
INSERT INTO "books" VALUES('book_d8c6b4a1', 'Hyperion', 'The Shrike', '978-0-553-28368-6', 3, 149);
INSERT INTO "books" VALUES('book_e2f8a1b5', 'Neuromancer', 'Case', '978-0-441-56959-5', 6, 158);
INSERT INTO "books" VALUES('book_f1b4c9d2', 'Foundation', 'Hari Seldon', '978-0-553-80371-9', 7, 152);
INSERT INTO "books" VALUES('book_cod7e2f6', 'Snow Crash', 'Hiro Protagonist', '978-0-553-38195-8', 5, 147);
INSERT INTO "books" VALUES('book_a9e1f5b8', 'Children of Time', 'Dr. Avrana Kern', '978-0-316-45228-8', 4, 133);
INSERT INTO "books" VALUES('book_b4a1c8d5', 'The Left Hand of Darkness', 'Genly Ai', '978-0-441-47812-5', 6, 112);
INSERT INTO "books" VALUES('book_d7e6f2b1', 'A Fire Upon the Deep', 'The Tines', '978-0-812-51528-2', 3, 126);
COMMIT;