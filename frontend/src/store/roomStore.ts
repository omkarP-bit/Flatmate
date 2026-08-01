import { create } from 'zustand';
import { Room, RoomMember } from '../types/room.types';
import { roomApi } from '../api/roomApi';

interface RoomState {
  rooms: Room[];
  activeRoomId: number | null;
  members: RoomMember[];
  loading: boolean;
  error: string | null;

  setActiveRoom: (roomId: number) => void;
  fetchMyRooms: () => Promise<void>;
  fetchMembers: (roomId: number) => Promise<void>;
  createRoom: (name: string, address?: string) => Promise<Room>;
  joinRoom: (code: string) => Promise<void>;
  updateRoom: (roomId: number, data: Partial<Pick<Room, 'name' | 'address'>>) => Promise<Room>;
  regenerateCode: (roomId: number) => Promise<string>;
  removeMember: (roomId: number, userId: string) => Promise<void>;
}

export const useRoomStore = create<RoomState>((set, get) => ({
  rooms: [],
  activeRoomId: null,
  members: [],
  loading: false,
  error: null,

  setActiveRoom: (roomId) => set({ activeRoomId: roomId }),

  fetchMyRooms: async () => {
    set({ loading: true, error: null });
    try {
      const rooms = await roomApi.getMine();
      const current = get().activeRoomId;
      const activeRoomId = current && rooms.some(r => r.id === current)
        ? current
        : rooms[0]?.id ?? null;
      set({ rooms, activeRoomId });
    } catch (e: any) {
      set({ error: e.message });
    } finally {
      set({ loading: false });
    }
  },

  fetchMembers: async (roomId) => {
    set({ loading: true });
    try {
      const members = await roomApi.getMembers(roomId);
      set({ members });
    } catch (e: any) {
      set({ error: e.message });
    } finally {
      set({ loading: false });
    }
  },

  createRoom: async (name, address) => {
    const room = await roomApi.create({ name, address });
    set(state => ({ rooms: [...state.rooms, room], activeRoomId: room.id }));
    return room;
  },

  joinRoom: async (code) => {
    const res = await roomApi.join({ room_code: code.toUpperCase() });
    const room = await roomApi.getById(res.room_id);
    set(state => ({
      rooms: state.rooms.some(r => r.id === room.id) ? state.rooms : [...state.rooms, room],
      activeRoomId: room.id,
    }));
  },

  removeMember: async (roomId, userId) => {
    await roomApi.removeMember(roomId, userId);
    set(state => ({ members: state.members.filter(m => m.user_id !== userId) }));
  },

  updateRoom: async (roomId, data) => {
    const room = await roomApi.update(roomId, data);
    set(state => ({
      rooms: state.rooms.map(r => (r.id === roomId ? { ...r, ...data } : r)),
    }));
    return room;
  },

  regenerateCode: async (roomId) => {
    const res = await roomApi.regenerateCode(roomId);
    set(state => ({
      rooms: state.rooms.map(r => (r.id === roomId ? { ...r, room_code: res.room_code } : r)),
    }));
    return res.room_code;
  },
}));