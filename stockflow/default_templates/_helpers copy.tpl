{{/*
Function to replace env variables
*/}}
{{- define "mychart.renderEnv" -}}
{{- $env := .env -}}

{{- range $k, $v := $env.plain }}
- name: {{ $k }}
  value: "{{ $v }}"
{{- end }}

{{- if $env.secret }}
{{- range $k, $v := $env.secret.keys }}
- name: {{ $k }}
  valueFrom:
    secretKeyRef:
      name: {{ $env.secret.name }}
      key: {{ $v }}
{{- end }}
{{- end }}
{{- end }}



{{/*
Expand the name of the chart.
*/}}
{{- define "stockflow.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "stockflow.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "stockflow.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "stockflow.labels" -}}
helm.sh/chart: {{ include "stockflow.chart" . }}
{{ include "stockflow.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "stockflow.selectorLabels" -}}
app.kubernetes.io/name: {{ include "stockflow.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "stockflow.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "stockflow.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
