---
layout: page
permalink: /publications-full/
title: "Publications"
lede: "Sorted most recent first. See Google Scholar for a complete and up-to-date list of citations."
noindex: true
sitemap: false
---

<!--
  WORK-IN-PROGRESS PAGE.
  This is the full publications listing rendered from _data/publications.yml.
  It is not linked from anywhere and is excluded from search engines via
  `noindex: true` (handled in _layouts/page.html). When the entries are
  fully reviewed, swap this file's permalink with /publications/ and update
  navigation if needed.
-->

<p style="margin-top: -16px; margin-bottom: 28px; font-size: 14px;">
  <a href="https://scholar.google.com/citations?user=g5CD7dQAAAAJ&hl=en">Google Scholar &rarr;</a>
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

{% assign sorted = site.data.publications | sort: "year" | reverse %}
{% assign current_year = "" %}

<div class="papers">
<ol>
{% for p in sorted %}
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
      <div class="venue">{{ p.venue }}{% if p.award %} &middot; <span class="award">{{ p.award }}</span>{% endif %}</div>
      <div class="links">
        {% if p.paper %}<a href="{{ p.paper }}">paper</a>{% endif %}
        {% if p.code %}<a href="{{ p.code }}">code</a>{% endif %}
        {% if p.site %}<a href="{{ p.site }}">site</a>{% endif %}
        {% if p.data %}<a href="{{ p.data }}">data</a>{% endif %}
        <a href="{{ '/files/bibtex/' | append: p.id | append: '.bib' | relative_url }}">bibtex</a>
      </div>
    </div>
  </li>
{% endfor %}
</ol>
</div>
