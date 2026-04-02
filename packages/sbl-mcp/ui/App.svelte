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
let isLoading = $state(true);

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

onMount(async () => {
  const instance = new App(
    { name: "SBL Article Viewer", version: "1.0.0" },
    { availableDisplayModes: ["inline"] },
    { autoResize: false },
  );

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

  instance.ontoolinput = () => {
    isLoading = true;
    error = null;
    article = null;
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
});
</script>

<main>
  {#if error}
    <div class="error">
      <p>{error}</p>
    </div>
  {:else if isLoading || !article}
    <div class="loading">
      <p>Laddar artikel...</p>
    </div>
  {:else}
    <article>
      <header>
        {#if article.image_files.length > 0}
          <img
            class="portrait"
            src={article.image_files[0]}
            alt={article.image_descriptions[0] ?? `Portr\u00e4tt av ${article.given_name} ${article.surname}`}
          />
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
              <span>F\u00f6dd: {article.birth_place}{#if article.birth_place_comment} ({article.birth_place_comment}){/if}</span>
            {/if}
            {#if article.birth_place && article.death_place}
              <span class="separator"> &middot; </span>
            {/if}
            {#if article.death_place}
              <span>D\u00f6d: {article.death_place}{#if article.death_place_comment} ({article.death_place_comment}){/if}</span>
            {/if}
          </p>
        {/if}
        {#if article.volume_number || article.page_number}
          <p class="reference">Band {article.volume_number}, s. {article.page_number}</p>
        {/if}
      </header>

      {#if article.cv}
        <section>
          <h2>Meriter</h2>
          <div class="content pre-wrap">{article.cv}</div>
        </section>
      {/if}

      {#if article.printed_works}
        <section>
          <h2>Tryckta arbeten</h2>
          <div class="content pre-wrap">{article.printed_works}</div>
        </section>
      {/if}

      {#if article.sources}
        <section>
          <h2>K\u00e4llor och litteratur</h2>
          <div class="content pre-wrap">{article.sources}</div>
        </section>
      {/if}

      {#if article.archive}
        <section>
          <h2>Arkivuppgifter</h2>
          <div class="content pre-wrap">{article.archive}</div>
        </section>
      {/if}

      <footer>
        {#if article.article_author}
          <p class="author">Artikelf\u00f6rfattare: {article.article_author}</p>
        {/if}
        {#if article.sbl_uri}
          <p><a href={article.sbl_uri} target="_blank" rel="noopener noreferrer">L\u00e4s hela artikeln p\u00e5 SBL</a></p>
        {/if}
        <p class="source">K\u00e4lla: Svenskt biografiskt lexikon (CC0)</p>
      </footer>
    </article>
  {/if}
</main>

<style>
  main {
    max-width: 700px;
    margin: 0 auto;
    padding: 1.5rem;
    font-family: inherit;
    line-height: 1.6;
  }

  .loading, .error {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 120px;
    color: var(--host-color-text-secondary, #666);
  }

  .error {
    color: var(--host-color-text-danger, #b91c1c);
  }

  article {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  header {
    position: relative;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--host-color-border, #ddd);
  }

  .portrait {
    float: right;
    max-width: 200px;
    margin: 0 0 0.75rem 1.25rem;
    border-radius: 4px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
  }

  h1 {
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0 0 0.25rem 0;
    line-height: 1.2;
  }

  .occupation {
    font-size: 1.1rem;
    color: var(--host-color-text-secondary, #555);
    margin-bottom: 0.25rem;
  }

  .lifespan {
    font-size: 1rem;
    color: var(--host-color-text-secondary, #555);
    margin-bottom: 0.15rem;
  }

  .places {
    font-size: 0.9rem;
    color: var(--host-color-text-secondary, #666);
    margin-bottom: 0.15rem;
  }

  .separator {
    color: var(--host-color-text-secondary, #999);
  }

  .reference {
    font-size: 0.85rem;
    color: var(--host-color-text-secondary, #888);
    margin-top: 0.5rem;
  }

  section {
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--host-color-border, #eee);
  }

  h2 {
    font-size: 1.15rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .content {
    font-size: 0.95rem;
    color: var(--host-color-text, #333);
  }

  .pre-wrap {
    white-space: pre-wrap;
  }

  footer {
    font-size: 0.85rem;
    color: var(--host-color-text-secondary, #666);
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  footer a {
    color: var(--host-color-accent, #0066cc);
    text-decoration: none;
  }

  footer a:hover {
    text-decoration: underline;
  }

  .author {
    font-style: italic;
  }

  .source {
    font-size: 0.8rem;
    color: var(--host-color-text-secondary, #999);
    margin-top: 0.25rem;
  }
</style>
