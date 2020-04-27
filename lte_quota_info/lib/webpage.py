"""Handle webpage generation."""
import os
import sys
import time
from jinja2 import Template


def create_html_document(config, node_stats):
    """Create html document based on stats."""
    try:
        template_path = config.get(
            'html_template', 'lte_quota_info.template')
        html_path = config.get(
            'html_path', '/var/www/128technology/lte_quota_info.html')
        if not os.path.isabs(template_path):
            template_path = os.path.join(sys.path[0], template_path)
        with open(template_path, 'r') as fd:
            template = Template(fd.read())
        with open(html_path, 'w') as fd:
            generated_timestamp_unixtime = int(time.time())
            generated_timestamp_utc = time.strftime(
                '%Y-%m-%d %H:%M:%S UTC',
                time.gmtime(generated_timestamp_unixtime))
            fd.write(template.render(
                node_stats=node_stats,
                generated_timestamp_utc=generated_timestamp_utc,
                generated_timestamp_unixtime=generated_timestamp_unixtime,
            ))
    except:
        raise
