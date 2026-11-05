---
layout: page
permalink: /publications/
title: "Publications"
lede: "Most recent first. Also on Google Scholar for citations."
redirect_from:
  - /publications-v2/
  - /publications-full/
---

<!--
  Rendered from _data/publications.yml, in file order (newest year first).
  Set `recent: true` on an entry to also feature it on the home page.
-->

<p style="margin-top: -16px; margin-bottom: 28px; font-size: 14px;">
  <a href="{{ site.author.googlescholar }}">Google Scholar &rarr;</a>
</p>

<style>
  .papers li.year-row {
    grid-template-columns: 1fr;
    border-top: 0;
    padding: 28px 0 4px;
  }
  .papers li.year-row:first-child { padding-top: 8px; }
  .papers li.year-row .year-label {
    font-family: var(--font-mono); font-size: 13px;
    color: var(--muted); letter-spacing: 0.06em;
  }
</style>

{% assign current_year = "" %}

<div class="papers">
<ol>
{% for p in site.data.publications %}
  {% if p.year != current_year %}
    <li class="year-row"><span class="year-label">{{ p.year }}</span></li>
    {% assign current_year = p.year %}
  {% endif %}
  <li>
    <div class="thumb {{ p.thumb_class | default: 'ph-default' }}"
         {% if p.thumb_image %} style="background-image:url('{{ p.thumb_image | relative_url }}');"{% endif %}
         id="{{ p.id }}"></div>
    <div>
      <div class="title">{{ p.title }}</div>
      <div class="authors">{{ p.authors }}</div>
      <div class="venue" title="{{ p.venue_full | escape }}">{{ p.venue }}{% if p.award %} &middot; <span class="award">{{ p.award }}</span>{% endif %}</div>
      <div class="links">
        {% if p.paper %}<a href="{{ p.paper }}">paper</a>{% endif %}
        {% if p.code %}<a href="{{ p.code }}">code</a>{% endif %}
        {% if p.site %}<a href="{{ p.site }}">site</a>{% endif %}
        {% if p.data %}<a href="{{ p.data }}">data</a>{% endif %}
        {% if p.bibtex %}<a href="{{ p.bibtex | relative_url }}">bibtex</a>{% endif %}
      </div>
    </div>
  </li>
{% endfor %}
</ol>
</div>
