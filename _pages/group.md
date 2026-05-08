---
layout: page
permalink: /group/
title: "Kerner Lab"
lede: "Current and former lab members. To inquire about joining the lab, please use the interest forms on the home page rather than emailing directly."
---

<style>
  .subpage .roster-list { list-style: none; padding: 0; margin: 0 0 24px; font-size: 14.5px; }
  .subpage .roster-list li { padding: 4px 0; }
  .subpage .roster-list a { color: var(--text); border-bottom: 1px dotted var(--muted); }
  .subpage .roster-list a:hover { color: var(--accent-text); border-bottom-color: var(--accent-text); }
  .subpage .roster-meta { color: var(--muted); font-size: 13.5px; }
</style>

<div class="section-heading">Postdocs &amp; research staff</div>
<ul class="roster-list">
{% for p in site.data.people.staff %}
  <li>
    {% if p.url and p.url != "" %}<a href="{{ p.url }}">{{ p.name }}</a>{% else %}{{ p.name }}{% endif %}
    <span class="roster-meta">— {{ p.role }}</span>
  </li>
{% endfor %}
</ul>

<div class="section-heading">PhD students</div>
<ul class="roster-list">
{% for p in site.data.people.phd %}
  <li>{% if p.url and p.url != "" %}<a href="{{ p.url }}">{{ p.name }}</a>{% else %}{{ p.name }}{% endif %}</li>
{% endfor %}
</ul>

{% if site.data.people.masters and site.data.people.masters.size > 0 %}
<div class="section-heading">M.S. students</div>
<ul class="roster-list">
{% for p in site.data.people.masters %}
  <li>{% if p.url and p.url != "" %}<a href="{{ p.url }}">{{ p.name }}</a>{% else %}{{ p.name }}{% endif %}</li>
{% endfor %}
</ul>
{% endif %}

{% if site.data.people.undergrad and site.data.people.undergrad.size > 0 %}
<div class="section-heading">Undergraduate students</div>
<ul class="roster-list">
{% for p in site.data.people.undergrad %}
  <li>{% if p.url and p.url != "" %}<a href="{{ p.url }}">{{ p.name }}</a>{% else %}{{ p.name }}{% endif %}</li>
{% endfor %}
</ul>
{% endif %}

{% if site.data.people.alumni and site.data.people.alumni.size > 0 %}
<div class="section-heading">Alumni</div>
<ul class="roster-list">
{% for p in site.data.people.alumni %}
  <li>
    {% if p.url and p.url != "" %}<a href="{{ p.url }}">{{ p.name }}</a>{% else %}{{ p.name }}{% endif %}
    {% if p.role %}<span class="roster-meta">— former {{ p.role }}{% if p.now %}, now {{ p.now }}{% endif %}</span>{% elsif p.now %}<span class="roster-meta">— now {{ p.now }}</span>{% endif %}
  </li>
{% endfor %}
</ul>
{% endif %}
