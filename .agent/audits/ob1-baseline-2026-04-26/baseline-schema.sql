CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
CREATE TABLE files (
                path TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                indexed_at_epoch INTEGER NOT NULL
            );
CREATE TABLE chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                section_title TEXT DEFAULT '',
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at_epoch INTEGER NOT NULL, last_touched INTEGER,
                FOREIGN KEY (file_path) REFERENCES files(path)
            );
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_chunks_file_path ON chunks(file_path);
CREATE VIRTUAL TABLE chunks_fts USING fts5(
                content,
                section_title,
                file_path UNINDEXED,
                content='chunks',
                content_rowid='id'
            )
/* chunks_fts(content,section_title,file_path) */;
CREATE TABLE IF NOT EXISTS 'chunks_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'chunks_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'chunks_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'chunks_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, content, section_title, file_path)
                VALUES (new.id, new.content, new.section_title, new.file_path);
            END;
CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content, section_title, file_path)
                VALUES ('delete', old.id, old.content, old.section_title, old.file_path);
            END;
CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content, section_title, file_path)
                VALUES ('delete', old.id, old.content, old.section_title, old.file_path);
                INSERT INTO chunks_fts(rowid, content, section_title, file_path)
                VALUES (new.id, new.content, new.section_title, new.file_path);
            END;
CREATE VIRTUAL TABLE vec_chunks USING vec0(
                embedding float[384]
            );
CREATE TABLE IF NOT EXISTS "vec_chunks_info" (key text primary key, value any);
CREATE TABLE IF NOT EXISTS "vec_chunks_chunks"(chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,size INTEGER NOT NULL,validity BLOB NOT NULL,rowids BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS "vec_chunks_rowids"(rowid INTEGER PRIMARY KEY AUTOINCREMENT,id,chunk_id INTEGER,chunk_offset INTEGER);
CREATE TABLE IF NOT EXISTS "vec_chunks_vector_chunks00"(rowid PRIMARY KEY,vectors BLOB NOT NULL);

-- ============================================================
-- Postgres schema (active backend via tunnel localhost:5433)
-- ============================================================
Usage: dotenv run [OPTIONS] [COMMANDLINE]...
Try 'dotenv run --help' for help.

Error: Invalid value: Invalid value for '-f' ".claude/scripts/.env" does not exist.
--
-- PostgreSQL database dump
--

\restrict klndmILsiibI8LQRuwcsbk8w6rUikE1BOg1lEme2GK9f5ebpO8K1VVeh01WkfgP

-- Dumped from database version 17.9 (Debian 17.9-1.pgdg12+1)
-- Dumped by pg_dump version 17.9 (Debian 17.9-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_sessions (
    id integer NOT NULL,
    session_id text NOT NULL,
    agent_session_id text NOT NULL,
    platform text NOT NULL,
    channel_id text NOT NULL,
    thread_id text NOT NULL,
    user_id text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    message_count integer DEFAULT 0,
    total_cost_usd double precision DEFAULT 0.0,
    status text DEFAULT 'active'::text,
    summary_folder_override text
);


--
-- Name: chat_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chat_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_sessions_id_seq OWNED BY public.chat_sessions.id;


--
-- Name: chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chunks (
    id integer NOT NULL,
    file_path text NOT NULL,
    start_line integer NOT NULL,
    end_line integer NOT NULL,
    section_title text DEFAULT ''::text,
    content text NOT NULL,
    content_hash text NOT NULL,
    created_at_epoch bigint NOT NULL,
    embedding public.vector(384),
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, ((COALESCE(content, ''::text) || ' '::text) || COALESCE(section_title, ''::text)))) STORED,
    last_touched bigint
);


--
-- Name: chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chunks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chunks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chunks_id_seq OWNED BY public.chunks.id;


--
-- Name: files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.files (
    path text NOT NULL,
    content_hash text NOT NULL,
    mtime_ns bigint NOT NULL,
    size_bytes bigint NOT NULL,
    indexed_at_epoch bigint NOT NULL
);


--
-- Name: heartbeat_threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.heartbeat_threads (
    id integer NOT NULL,
    channel_id text NOT NULL,
    thread_ts text NOT NULL,
    alert_text text NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: heartbeat_threads_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.heartbeat_threads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: heartbeat_threads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.heartbeat_threads_id_seq OWNED BY public.heartbeat_threads.id;


--
-- Name: meta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.meta (
    key text NOT NULL,
    value text
);


--
-- Name: chat_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions ALTER COLUMN id SET DEFAULT nextval('public.chat_sessions_id_seq'::regclass);


--
-- Name: chunks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunks ALTER COLUMN id SET DEFAULT nextval('public.chunks_id_seq'::regclass);


--
-- Name: heartbeat_threads id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.heartbeat_threads ALTER COLUMN id SET DEFAULT nextval('public.heartbeat_threads_id_seq'::regclass);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_session_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_session_id_key UNIQUE (session_id);


--
-- Name: chunks chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_pkey PRIMARY KEY (id);


--
-- Name: files files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (path);


--
-- Name: heartbeat_threads heartbeat_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.heartbeat_threads
    ADD CONSTRAINT heartbeat_threads_pkey PRIMARY KEY (id);


--
-- Name: meta meta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meta
    ADD CONSTRAINT meta_pkey PRIMARY KEY (key);


--
-- Name: idx_chunks_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_embedding ON public.chunks USING hnsw (embedding public.vector_l2_ops) WHERE (embedding IS NOT NULL);


--
-- Name: idx_chunks_file_path; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_file_path ON public.chunks USING btree (file_path);


--
-- Name: idx_chunks_search_vector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_search_vector ON public.chunks USING gin (search_vector);


--
-- Name: idx_hb_channel_thread; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_hb_channel_thread ON public.heartbeat_threads USING btree (channel_id, thread_ts);


--
-- Name: idx_platform_thread; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_platform_thread ON public.chat_sessions USING btree (platform, channel_id, thread_id);


--
-- Name: chunks chunks_file_path_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_file_path_fkey FOREIGN KEY (file_path) REFERENCES public.files(path);


--
-- PostgreSQL database dump complete
--

\unrestrict klndmILsiibI8LQRuwcsbk8w6rUikE1BOg1lEme2GK9f5ebpO8K1VVeh01WkfgP

