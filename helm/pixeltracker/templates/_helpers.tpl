{{/*
Expand the name of the chart.
*/}}
{{- define "pixeltracker.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "pixeltracker.fullname" -}}
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
{{- define "pixeltracker.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "pixeltracker.labels" -}}
helm.sh/chart: {{ include "pixeltracker.chart" . }}
{{ include "pixeltracker.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: pixeltracker
{{- end }}

{{/*
Selector labels
*/}}
{{- define "pixeltracker.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pixeltracker.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "pixeltracker.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "pixeltracker.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the image name
*/}}
{{- define "pixeltracker.image" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.image.registry -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- $variant := .Values.image.variant -}}
{{- if $registry }}
{{- printf "%s/%s:%s-%s" $registry $repository $tag $variant }}
{{- else }}
{{- printf "%s:%s-%s" $repository $tag $variant }}
{{- end }}
{{- end }}

{{/*
ConfigMap name
*/}}
{{- define "pixeltracker.configmapName" -}}
{{- printf "%s-config" (include "pixeltracker.fullname" .) }}
{{- end }}

{{/*
Secrets name
*/}}
{{- define "pixeltracker.secretsName" -}}
{{- printf "%s-secrets" (include "pixeltracker.fullname" .) }}
{{- end }}

{{/*
PVC names for different volumes
*/}}
{{- define "pixeltracker.pvcDataName" -}}
{{- printf "%s-data" (include "pixeltracker.fullname" .) }}
{{- end }}

{{- define "pixeltracker.pvcLogsName" -}}
{{- printf "%s-logs" (include "pixeltracker.fullname" .) }}
{{- end }}

{{- define "pixeltracker.pvcConfigName" -}}
{{- printf "%s-config" (include "pixeltracker.fullname" .) }}
{{- end }}

{{- define "pixeltracker.pvcCacheName" -}}
{{- printf "%s-cache" (include "pixeltracker.fullname" .) }}
{{- end }}

{{/*
Redis connection string
*/}}
{{- define "pixeltracker.redisUrl" -}}
{{- if .Values.redis.external.enabled }}
{{- printf "redis://%s:%d" .Values.redis.external.host (.Values.redis.external.port | int) }}
{{- else }}
{{- printf "redis://%s-redis-master:6379" .Release.Name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL connection string
*/}}
{{- define "pixeltracker.postgresUrl" -}}
{{- if .Values.postgresql.external.enabled }}
{{- printf "postgresql://%s:%s@%s:%d/%s" .Values.postgresql.external.username .Values.postgresql.external.password .Values.postgresql.external.host (.Values.postgresql.external.port | int) .Values.postgresql.external.database }}
{{- else }}
{{- printf "postgresql://%s:%s@%s-postgresql:5432/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password .Release.Name .Values.postgresql.auth.database }}
{{- end }}
{{- end }}

{{/*
MongoDB connection string
*/}}
{{- define "pixeltracker.mongoUrl" -}}
{{- if .Values.mongodb.external.enabled }}
{{- printf "mongodb://%s:%s@%s:%d/%s" .Values.mongodb.external.username .Values.mongodb.external.password .Values.mongodb.external.host (.Values.mongodb.external.port | int) .Values.mongodb.external.database }}
{{- else }}
{{- printf "mongodb://%s:%s@%s-mongodb:27017/%s" .Values.mongodb.auth.username .Values.mongodb.auth.password .Release.Name .Values.mongodb.auth.database }}
{{- end }}
{{- end }}

{{/*
Environment-specific configuration merge
*/}}
{{- define "pixeltracker.environmentConfig" -}}
{{- $env := .Values.environment -}}
{{- $envConfig := index .Values $env -}}
{{- if $envConfig }}
{{- $merged := mergeOverwrite .Values.configMap.data $envConfig.configMap.data | default .Values.configMap.data -}}
{{- toYaml $merged }}
{{- else }}
{{- toYaml .Values.configMap.data }}
{{- end }}
{{- end }}

{{/*
Storage class helper
*/}}
{{- define "pixeltracker.storageClass" -}}
{{- $storageClass := .Values.global.storageClass | default .Values.persistence.storageClass -}}
{{- if $storageClass }}
storageClassName: {{ $storageClass }}
{{- end }}
{{- end }}

{{/*
Image pull secrets
*/}}
{{- define "pixeltracker.imagePullSecrets" -}}
{{- if .Values.global.imagePullSecrets }}
imagePullSecrets:
{{- range .Values.global.imagePullSecrets }}
  - name: {{ . }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Environment variables for database connections
*/}}
{{- define "pixeltracker.databaseEnvVars" -}}
{{- if .Values.redis.enabled }}
- name: PIXELTRACKER_REDIS_HOST
  value: {{ include "pixeltracker.redisHost" . | quote }}
- name: PIXELTRACKER_REDIS_PORT
  value: {{ include "pixeltracker.redisPort" . | quote }}
{{- if .Values.redis.auth.enabled }}
- name: PIXELTRACKER_REDIS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Release.Name }}-redis
      key: redis-password
{{- end }}
{{- end }}
{{- if .Values.postgresql.enabled }}
- name: PIXELTRACKER_POSTGRES_HOST
  value: {{ include "pixeltracker.postgresHost" . | quote }}
- name: PIXELTRACKER_POSTGRES_PORT
  value: {{ include "pixeltracker.postgresPort" . | quote }}
- name: PIXELTRACKER_POSTGRES_DB
  value: {{ .Values.postgresql.auth.database | quote }}
- name: PIXELTRACKER_POSTGRES_USER
  value: {{ .Values.postgresql.auth.username | quote }}
- name: PIXELTRACKER_POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Release.Name }}-postgresql
      key: password
{{- end }}
{{- if .Values.mongodb.enabled }}
- name: PIXELTRACKER_MONGODB_HOST
  value: {{ include "pixeltracker.mongoHost" . | quote }}
- name: PIXELTRACKER_MONGODB_PORT
  value: {{ include "pixeltracker.mongoPort" . | quote }}
- name: PIXELTRACKER_MONGODB_DB
  value: {{ .Values.mongodb.auth.database | quote }}
- name: PIXELTRACKER_MONGODB_USER
  value: {{ .Values.mongodb.auth.username | quote }}
- name: PIXELTRACKER_MONGODB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Release.Name }}-mongodb
      key: mongodb-password
{{- end }}
{{- end }}

{{/*
Redis host helper
*/}}
{{- define "pixeltracker.redisHost" -}}
{{- if .Values.redis.external.enabled }}
{{- .Values.redis.external.host }}
{{- else }}
{{- printf "%s-redis-master" .Release.Name }}
{{- end }}
{{- end }}

{{/*
Redis port helper
*/}}
{{- define "pixeltracker.redisPort" -}}
{{- if .Values.redis.external.enabled }}
{{- .Values.redis.external.port }}
{{- else }}
{{- "6379" }}
{{- end }}
{{- end }}

{{/*
PostgreSQL host helper
*/}}
{{- define "pixeltracker.postgresHost" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.host }}
{{- else }}
{{- printf "%s-postgresql" .Release.Name }}
{{- end }}
{{- end }}

{{/*
PostgreSQL port helper
*/}}
{{- define "pixeltracker.postgresPort" -}}
{{- if .Values.postgresql.external.enabled }}
{{- .Values.postgresql.external.port }}
{{- else }}
{{- "5432" }}
{{- end }}
{{- end }}

{{/*
MongoDB host helper
*/}}
{{- define "pixeltracker.mongoHost" -}}
{{- if .Values.mongodb.external.enabled }}
{{- .Values.mongodb.external.host }}
{{- else }}
{{- printf "%s-mongodb" .Release.Name }}
{{- end }}
{{- end }}

{{/*
MongoDB port helper
*/}}
{{- define "pixeltracker.mongoPort" -}}
{{- if .Values.mongodb.external.enabled }}
{{- .Values.mongodb.external.port }}
{{- else }}
{{- "27017" }}
{{- end }}
{{- end }}
