import { defineStore } from 'pinia'
import { LocalStorage } from 'quasar'
import { api } from 'boot/axios'

export const useTeamStore = defineStore('team', {
  state: () => ({
    teams: [],
    currentTeamId: null,
    lastUsedTeamId: LocalStorage.getItem('lastTeamId') || null,
  }),
  getters: {
    currentTeam(state) {
      return state.teams.find(t => String(t.id) === String(state.currentTeamId)) || null
    },
  },
  actions: {
    async fetchTeams() {
  const { data } = await api.get('/teams/', { params: { page: 1, page_size: 100 } })
  this.teams = Array.isArray(data?.items) ? data.items : []
  return this.teams
    },
    setCurrentTeam(id) {
      this.currentTeamId = id
      this.lastUsedTeamId = id
      LocalStorage.set('lastTeamId', id)
    },
  },
})
