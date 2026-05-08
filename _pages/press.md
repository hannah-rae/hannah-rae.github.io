---
layout: page
permalink: /press/
title: "In the press"
lede: "Articles, podcasts, and features about the lab's research, plus a few op-eds and essays."
---

<div class="section-heading">Features &amp; profiles</div>
<ul class="press-list">
{% for p in site.data.press %}
  {% unless p.op_ed %}
  <li>
    <span class="source">{{ p.source }} &middot; {{ p.date | date: "%b %Y" }}</span>
    <span class="head"><a href="{{ p.url }}">{{ p.title }}</a></span>
  </li>
  {% endunless %}
{% endfor %}
</ul>

<div class="section-heading">Op-eds &amp; essays</div>
<ul class="press-list">
{% for p in site.data.press %}
  {% if p.op_ed %}
  <li>
    <span class="source">{{ p.source }} &middot; {{ p.date | date: "%b %Y" }}</span>
    <span class="head"><a href="{{ p.url }}">{{ p.title }}</a></span>
  </li>
  {% endif %}
{% endfor %}
</ul>
