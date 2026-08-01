import { roomClient } from './client';
import { Room, RoomMember, RoomCreate, RoomJoin, RoomUpdate } from '../types/room.types';

export const roomApi = {
  create: (data: RoomCreate) =>
    roomClient.post<Room>('/rooms', data).then(r => r.data),

  join: (data: RoomJoin) =>
    roomClient.post<{ message: string; room_id: number }>('/rooms/join', data).then(r => r.data),

  getMine: () =>
    roomClient.get<Room[]>('/rooms/mine').then(r => r.data),

  getById: (roomId: number) =>
    roomClient.get<Room>(`/rooms/${roomId}`).then(r => r.data),

  getMembers: (roomId: number) =>
    roomClient.get<RoomMember[]>(`/rooms/${roomId}/members`).then(r => r.data),

  update: (roomId: number, data: RoomUpdate) =>
    roomClient.patch<Room>(`/rooms/${roomId}`, data).then(r => r.data),

  regenerateCode: (roomId: number) =>
    roomClient.post<{ message: string; room_code: string }>(`/rooms/${roomId}/regenerate-code`).then(r => r.data),

  removeMember: (roomId: number, userId: string) =>
    roomClient.delete<{ message: string }>(`/rooms/${roomId}/members/${userId}`).then(r => r.data),
};