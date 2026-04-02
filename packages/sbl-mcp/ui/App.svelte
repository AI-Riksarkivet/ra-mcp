<script lang="ts">
import { onMount } from "svelte";
import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";

interface SBLArticle {
  article_id: number;
  surname: string;
  given_name: string;
  gender: string;
  article_type: string;
  occupation: string;
  birth_year: number | null;
  birth_month: number | null;
  birth_day: number | null;
  birth_place: string;
  birth_place_comment: string;
  death_year: number | null;
  death_month: number | null;
  death_day: number | null;
  death_place: string;
  death_place_comment: string;
  cv: string;
  archive: string;
  printed_works: string;
  sources: string;
  article_author: string;
  volume_number: string;
  page_number: string;
  sbl_uri: string;
  image_files: string[];
  image_descriptions: string[];
}

let app = $state<App | null>(null);
let hostContext = $state<McpUiHostContext | undefined>();
let article = $state<SBLArticle | null>(null);
let error = $state<string | null>(null);
let isLoading = $state(false);

function formatDate(year: number | null, month: number | null, day: number | null): string {
  if (!year) return "";
  const parts: string[] = [];
  if (day) parts.push(String(day));
  if (month) {
    const months = [
      "januari", "februari", "mars", "april", "maj", "juni",
      "juli", "augusti", "september", "oktober", "november", "december",
    ];
    parts.push(months[month - 1] ?? String(month));
  }
  parts.push(String(year));
  return parts.join(" ");
}

function formatLifespan(a: SBLArticle): string {
  const birth = formatDate(a.birth_year, a.birth_month, a.birth_day);
  const death = formatDate(a.death_year, a.death_month, a.death_day);
  if (!birth && !death) return "";
  if (birth && !death) return `f. ${birth}`;
  if (!birth && death) return `d. ${death}`;
  return `${birth}\u2013${death}`;
}

$effect(() => {
  if (hostContext?.theme) applyDocumentTheme(hostContext.theme);
  if (hostContext?.styles?.variables) applyHostStyleVariables(hostContext.styles.variables);
  if (hostContext?.styles?.css?.fonts) applyHostFonts(hostContext.styles.css.fonts);
});

$effect(() => {
  const isFullscreen = hostContext?.displayMode === "fullscreen";
  if (!app || isFullscreen) return;
  app.sendSizeChanged({ height: 600 });
});

onMount(async () => {
  const instance = new App(
    { name: "SBL Article Viewer", version: "1.0.0" },
    { availableDisplayModes: ["inline", "fullscreen"] },
    { autoResize: false },
  );

  instance.ontoolinputpartial = () => {
    if (!article) isLoading = true;
  };

  instance.ontoolinput = () => {
    isLoading = true;
    error = null;
    article = null;
  };

  instance.ontoolresult = (result) => {
    isLoading = false;
    if (result.isError) {
      error = result.content?.map((c: any) => ("text" in c ? c.text : "")).join(" ") ?? "Unknown error";
      return;
    }
    const sc = result.structuredContent as SBLArticle | undefined;
    if (sc) {
      article = sc;
      error = null;
    }
  };

  instance.ontoolcancelled = () => {
    isLoading = false;
  };

  instance.onerror = (err) => {
    console.error("App error:", err);
    error = err.message;
  };

  instance.onhostcontextchanged = (params) => {
    hostContext = { ...hostContext, ...params };
  };

  instance.onteardown = async () => {
    return {};
  };

  await instance.connect();
  app = instance;
  hostContext = instance.getHostContext();
  instance.requestDisplayMode({ mode: "fullscreen" }).catch(() => {});
});
</script>

<main>
  {#if error}
    <div class="error">
      <p>{error}</p>
    </div>
  {:else if isLoading}
    <div class="loading">
      <p>Laddar artikel...</p>
    </div>
  {:else if !article}
    <div class="loading">
      <p>Väntar på artikeldata...</p>
    </div>
  {:else}
    <article>
      <header>
        {#if Array.isArray(article.image_files) && article.image_files.length > 0}
          <img
            class="portrait"
            src={article.image_files[0]}
            alt={article.image_descriptions?.[0] ?? `Porträtt av ${article.given_name} ${article.surname}`}
          />
          {#if article.image_descriptions?.[0]}
            <span class="portrait-caption">{article.image_descriptions[0]}</span>
          {/if}
        {/if}
        <h1>{article.given_name} {article.surname}</h1>
        {#if article.occupation}
          <p class="occupation">{article.occupation}</p>
        {/if}
        {#if formatLifespan(article)}
          <p class="lifespan">{formatLifespan(article)}</p>
        {/if}
        {#if article.birth_place || article.death_place}
          <p class="places">
            {#if article.birth_place}
              <span>f. {article.birth_place}{#if article.birth_place_comment} ({article.birth_place_comment}){/if}</span>
            {/if}
            {#if article.birth_place && article.death_place}
              <span class="separator"> &middot; </span>
            {/if}
            {#if article.death_place}
              <span>d. {article.death_place}{#if article.death_place_comment} ({article.death_place_comment}){/if}</span>
            {/if}
          </p>
        {/if}
        {#if article.volume_number || article.page_number}
          <span class="reference">SBL band {article.volume_number}, s. {article.page_number}</span>
        {/if}
      </header>

      {#if article.cv || article.printed_works || article.sources || article.archive}
        <nav class="section-nav">
          {#if article.cv}<a href="#meriter">Meriter</a>{/if}
          {#if article.printed_works}<a href="#tryckta">Tryckta arbeten</a>{/if}
          {#if article.sources}<a href="#kallor">Källor</a>{/if}
          {#if article.archive}<a href="#arkiv">Arkivuppgifter</a>{/if}
        </nav>
      {/if}

      {#if article.cv}
        <section id="meriter">
          <h2>Meriter</h2>
          <div class="content pre-wrap">{article.cv}</div>
        </section>
      {/if}

      {#if article.printed_works}
        <section id="tryckta">
          <h2>Tryckta arbeten</h2>
          <div class="content pre-wrap">{article.printed_works}</div>
        </section>
      {/if}

      {#if article.sources}
        <section id="kallor">
          <h2>Källor och litteratur</h2>
          <div class="content pre-wrap">{article.sources}</div>
        </section>
      {/if}

      {#if article.archive}
        <section id="arkiv">
          <h2>Arkivuppgifter</h2>
          <div class="content pre-wrap">{article.archive}</div>
        </section>
      {/if}

      <footer>
        {#if article.article_author}
          <p class="author">Artikelförfattare: {article.article_author}</p>
        {/if}
        {#if article.sbl_uri}
          <p><a href={article.sbl_uri} target="_blank" rel="noopener noreferrer">Läs hela artikeln på SBL &rarr;</a></p>
        {/if}
        <p class="source">Källa: Svenskt biografiskt lexikon (CC0)</p>
      </footer>
    </article>
  {/if}
</main>

<style>
  main {
    max-width: 720px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
    min-height: 100%;
    overflow-y: auto;
  }

  .loading, .error {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    color: var(--sbl-text-secondary, #666);
    font-size: 0.95rem;
  }
  .error { color: #dc2626; }

  article {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  /* Header */
  header {
    position: relative;
    padding-bottom: 1.25rem;
    margin-bottom: 0.25rem;
    border-bottom: 2px solid var(--sbl-border, #d6d3d1);
  }

  .portrait {
    float: right;
    width: 180px;
    max-width: 40%;
    margin: 0 0 0.75rem 1.5rem;
    border-radius: 3px;
    box-shadow: var(--sbl-portrait-shadow, 0 2px 8px rgba(0,0,0,0.12));
    filter: saturate(0.9);
  }
  .portrait:hover { filter: saturate(1); }

  .portrait-caption {
    float: right;
    clear: right;
    width: 180px;
    max-width: 40%;
    margin: -0.5rem 0 0.75rem 1.5rem;
    font-size: 0.75rem;
    color: var(--sbl-text-muted, #a8a29e);
    line-height: 1.3;
    text-align: center;
  }

  h1 {
    font-family: var(--sbl-font-serif, Georgia, serif);
    font-size: 1.85rem;
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.01em;
    margin-bottom: 0.3rem;
  }

  .occupation {
    font-size: 1.05rem;
    color: var(--sbl-text-secondary, #57534e);
    margin-bottom: 0.35rem;
    font-style: italic;
  }

  .lifespan {
    font-size: 0.95rem;
    color: var(--sbl-text-secondary, #57534e);
    letter-spacing: 0.02em;
    margin-bottom: 0.2rem;
  }

  .places {
    font-size: 0.85rem;
    color: var(--sbl-text-muted, #a8a29e);
  }
  .separator { color: var(--sbl-text-muted, #a8a29e); }

  .reference {
    display: inline-block;
    margin-top: 0.6rem;
    font-size: 0.8rem;
    color: var(--sbl-text-muted, #a8a29e);
    background: var(--sbl-bg-card, #f4f3ef);
    padding: 0.2rem 0.6rem;
    border-radius: 3px;
    letter-spacing: 0.03em;
  }

  /* Section nav */
  .section-nav {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--sbl-border-light, #e7e5e4);
    margin-bottom: 0;
    overflow-x: auto;
  }
  .section-nav a {
    padding: 0.5rem 0.85rem;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--sbl-text-secondary, #57534e);
    text-decoration: none;
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    transition: color 0.15s, border-color 0.15s;
  }
  .section-nav a:hover {
    color: var(--sbl-text, #1c1917);
    border-bottom-color: var(--sbl-accent, #1e40af);
  }

  /* Sections */
  section {
    padding: 1.25rem 0;
    border-bottom: 1px solid var(--sbl-border-light, #e7e5e4);
  }
  section:last-of-type { border-bottom: none; }

  h2 {
    font-family: var(--sbl-font-serif, Georgia, serif);
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--sbl-text, #1c1917);
    margin-bottom: 0.6rem;
    letter-spacing: 0.01em;
  }

  .content {
    font-size: 0.92rem;
    line-height: 1.75;
    color: var(--sbl-text, #1c1917);
  }

  .pre-wrap {
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* Footer */
  footer {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--sbl-border-light, #e7e5e4);
    font-size: 0.82rem;
    color: var(--sbl-text-muted, #a8a29e);
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  footer a {
    color: var(--sbl-accent, #1e40af);
    text-decoration: none;
    font-weight: 500;
  }
  footer a:hover { text-decoration: underline; }

  .author { font-style: italic; }

  .source {
    font-size: 0.75rem;
    color: var(--sbl-text-muted, #a8a29e);
    margin-top: 0.15rem;
  }

  @media (max-width: 500px) {
    main { padding: 1rem; }
    h1 { font-size: 1.5rem; }
    .portrait, .portrait-caption {
      float: none;
      width: 100%;
      max-width: 240px;
      margin: 0 auto 1rem auto;
      display: block;
      text-align: center;
    }
  }
</style>
