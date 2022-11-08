{% set base_directory = "/etc/snmp" %}
{% set config_directory = "conf.d" %}
{% set lte_config = "128T-snmpd-lte.conf" %}
{% set global_config = "128T-snmpd.conf" %}
{% set include_config = "128T-include.conf" %}
{% set lte_script = "/usr/sbin/snmp_lte_stats.py" %}
{% set override_file = "/etc/systemd/system/128T-snmpd.service.d/override.conf" %}

128T snmpd config directory:
  file.directory:
    - name: {{ base_directory }}/{{ config_directory }}
    - mode: 755

128T snmpd include config:
  file.managed:
    - name: {{ base_directory }}/{{ include_config }}
    - contents:
      - includeDir	{{ base_directory }}/{{ config_directory }}
    - mode: 400

128T snmpd lte config:
  file.managed:
    - name: {{ base_directory }}/{{ lte_config }}
    - contents:
      - pass .1.3.6.1.4.1.45956.1.100 {{ lte_script }}
    - mode: 400

lte script:
  file.managed:
    - name: {{ lte_script }}
    - mode: 755
    - source: salt://snmp_lte_stats.py

/etc/systemd/system/128T-snmpd.service.d:
  file.directory:
    - mode: 755

128T-snmpd.service:
  file.managed:
    - name: {{ override_file }}
    - contents: |
        [Service]
        ExecStart=
        ExecStart=/usr/sbin/snmpd \
          $OPTIONS -f \
          $IF_MIB_OVERRIDES \
          -C -c {{ base_directory }}/{{ include_config }} \
          -p /run/128T-snmpd.pid
  module.run:
    - name: service.systemctl_reload
    - onchanges:
      - file: {{ override_file }}
  service.running:
    - watch:
      - file: {{ base_directory }}/{{ lte_config }}
      - file: {{ lte_script }}
      - file: {{ override_file }}
