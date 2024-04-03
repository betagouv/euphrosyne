Directory contain web components.
To use typescript, the files must be processed with Webpack. Thus, we store them here and
create an entry in webpack config.
Then, the files will be available in html pages with `static` template tag.
For example, the file 'typeahead.ts' will be available with `{% static 'web-components/typeahead.js' %}`.
