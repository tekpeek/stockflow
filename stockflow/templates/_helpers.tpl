{{/*
Function to replace env variables
*/}}
{{- define "mychart.renderEnv" -}}
{{- $env := .env -}}

{{- range $key, $value := $env.plain }}
- name: {{ $key }}
  value: "{{ $value }}"
{{- end }}

{{- if $env.secret }}
{{- range $item := $env.secret }}
- name: {{ $item.name }}
  valueFrom:
    secretKeyRef:
      name: {{ $item.secret }}
      key: {{ $item.key }}
{{- end }}
{{- end }}

{{- if $env.configmap }}
{{- range $item := $env.configmap }}
- name: {{ $item.name }}
  valueFrom:
    configMapKeyRef:
      name: {{ $item.configmap }}
      key: {{ $item.key }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Function to replace ports
*/}}
{{- define "mychart.renderPorts" -}}
{{- $ports := .ports -}}
{{- range $item := $ports }}
- name: {{ $item.name }}
  containerPort: {{ $item.containerPort }}
{{- end }}
{{- end }}

{{/*
Function to replace volumeMounts
*/}}
{{- define "mychart.volumeMounts" -}}
{{- $volumeMounts := .volumeMounts -}}
{{- range $item := $volumeMounts }}
- name: {{ $item.name }}
  mountPath: {{ $item.mountPath }}
  subPath: {{ $item.subPath }}
{{- end }}
{{- end }}

{{/*
Function to replace volumes
*/}}
{{- define "mychart.volumes" -}}
{{- $volumes := .volumes -}}
{{- if $volumes.configmap }}
{{- range $item := $volumes.configmap }}
- name: {{ $item.name }}
  configMap:
    name: {{ $item.configmap }}
{{- end }}
{{- end }}
{{- end }}


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

{{/*
Expand the name of the chart.
*/}}
{{- define "stockflow.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}