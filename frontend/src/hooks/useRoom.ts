import { useEffect } from 'react';
import { useRoomStore } from '../store/roomStore';
import { useAuthStore } from '../store/authStore';

export function useRoom() {
  const { user } = useAuthStore();
  const {
    rooms, activeRoomId, members, loading, error,
    setActiveRoom, fetchMyRooms, fetchMembers,
    createRoom, joinRoom, removeMember, updateRoom, regenerateCode,
  } = useRoomStore();

  const activeRoom = rooms.find(r => r.id === activeRoomId) ?? null;

  const myMembership = members.find(m => m.user_id === user?.id) ?? null;
  const isAdmin = myMembership?.role === 'admin';

  useEffect(() => {
    if (activeRoomId) fetchMembers(activeRoomId);
  }, [activeRoomId]);

  const handleCreate = async (name: string, address?: string) => {
    const room = await createRoom(name, address);
    await fetchMembers(room.id);
    return room;
  };

  const handleJoin = async (code: string) => {
    await joinRoom(code);
  };

  const handleRemoveMember = async (userId: string) => {
    if (!activeRoomId) return;
    await removeMember(activeRoomId, userId);
  };

  const handleUpdateRoom = async (data: { name?: string; address?: string }) => {
    if (!activeRoomId) return;
    return updateRoom(activeRoomId, data);
  };

  const handleRegenerateCode = async () => {
    if (!activeRoomId) return '';
    return regenerateCode(activeRoomId);
  };

  const handleLeave = async () => {
    if (!activeRoomId || !user) return;
    await removeMember(activeRoomId, user.id);
    await fetchMyRooms();
  };

  return {
    rooms, activeRoom, activeRoomId, members,
    myMembership, isAdmin,
    loading, error,
    setActiveRoom,
    handleCreate, handleJoin, handleRemoveMember,
    handleUpdateRoom, handleRegenerateCode, handleLeave,
  };
}