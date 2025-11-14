<template>
  <q-page padding>
    <div class="row items-center q-col-gutter-md q-mb-md">
      <div class="col-auto text-h6">团队关联项目</div>
      <div class="col-auto"><TeamSelector @change="reload" /></div>
    </div>
    <q-card flat bordered>
      <q-card-section>当前团队：{{ team?.name || '-' }}（ID: {{ teamId || '-' }}）</q-card-section>
      <q-separator />
      <q-card-section>这里展示和管理团队关联的项目（占位）。</q-card-section>
    </q-card>
  </q-page>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LocalStorage } from 'quasar'
import { useTeamStore } from 'stores/team/useTeamStore'
import TeamSelector from 'components/TeamSelector.vue'

const route = useRoute()
const router = useRouter()
const store = useTeamStore()

const teamId = computed(() => store.currentTeamId)
const team = computed(() => store.currentTeam)

async function ensureTeam() {
  let id = route.query.teamId || LocalStorage.getItem('lastTeamId')
  if (!id) {
    const list = store.teams.length ? store.teams : await store.fetchTeams()
    id = list[0]?.id
  }
  if (id && String(id) !== String(store.currentTeamId)) store.setCurrentTeam(id)
  if (id && route.query.teamId !== String(id)) router.replace({ query: { ...route.query, teamId: String(id) } })
}

function reload() {}

onMounted(async () => {
  if (!store.teams.length) await store.fetchTeams()
  await ensureTeam()
})
</script>
