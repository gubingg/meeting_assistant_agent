import { createRouter, createWebHistory } from 'vue-router';

import HomeView from '@/views/HomeView.vue';
import ProjectWorkspaceView from '@/views/ProjectWorkspaceView.vue';
import ProjectTodosView from '@/views/ProjectTodosView.vue';
import ProjectQaView from '@/views/ProjectQaView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/projects/:projectId', name: 'project-workspace', component: ProjectWorkspaceView },
    { path: '/projects/:projectId/todos', name: 'project-todos', component: ProjectTodosView },
    { path: '/projects/:projectId/qa', name: 'project-qa', component: ProjectQaView },
  ],
});

export default router;
