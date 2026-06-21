import React, { useState, useEffect } from 'react';
import './AdminPanel.css';

const API_BASE = 'http://localhost:8000';

interface User {
  id: string;
  username: string;
  full_name: string;
  branch_code: string | null;
  role: string | null;
}

interface AdminPanelProps {
  onClose: () => void;
  onUserAdded: () => void;
}

export function AdminPanel({ onClose, onUserAdded }: AdminPanelProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>('');

  // Create User State
  const [newUsername, setNewUsername] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newBranch, setNewBranch] = useState('HN');

  // Permissions State
  const [tableAccess, setTableAccess] = useState<string>('ALLOW');
  const [rowFilter, setRowFilter] = useState<string>('');
  const [phoneMask, setPhoneMask] = useState<string>('NONE');
  const [idMask, setIdMask] = useState<string>('NONE');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/admin/users`);
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: newUsername,
          full_name: newFullName,
          branch_code: newBranch || null
        })
      });
      if (res.ok) {
        setMessage('Tạo người dùng thành công!');
        setNewUsername('');
        setNewFullName('');
        fetchUsers();
        onUserAdded();
      } else {
        const err = await res.json();
        setMessage(`Lỗi: ${err.detail}`);
      }
    } catch (error) {
      setMessage('Lỗi mạng');
    }
    setLoading(false);
  };

  const handleSelectUser = async (userId: string) => {
    setSelectedUserId(userId);
    setMessage('');
    if (!userId) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${userId}/permissions`);
      if (res.ok) {
        const data = await res.json();
        setTableAccess(data.table_access || 'ALLOW');
        setRowFilter(data.row_filter || '');
        setPhoneMask(data.phone_mask || 'NONE');
        setIdMask(data.id_mask || 'NONE');
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleUpdatePermissions = async () => {
    if (!selectedUserId) return;
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${selectedUserId}/permissions`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          table_access: tableAccess,
          row_filter: rowFilter || null,
          phone_mask: phoneMask,
          id_mask: idMask
        })
      });
      if (res.ok) {
        setMessage('Cập nhật quyền thành công!');
      } else {
        setMessage('Lỗi khi cập nhật quyền');
      }
    } catch (e) {
      setMessage('Lỗi mạng');
    }
    setLoading(false);
  };

  return (
    <div className="admin-modal-overlay">
      <div className="admin-modal">
        <div className="admin-header">
          <h2>Quản lý User & Quyền</h2>
          <button onClick={onClose} className="close-btn">&times;</button>
        </div>

        {message && <div className="admin-message">{message}</div>}

        <div className="admin-content">
          {/* Cột 1: Thêm User */}
          <div className="admin-section">
            <h3>Tạo User Mới</h3>
            <form onSubmit={handleCreateUser} className="admin-form">
              <label>
                Username:
                <input required value={newUsername} onChange={e => setNewUsername(e.target.value)} placeholder="vd: nguyen_van_a" />
              </label>
              <label>
                Họ Tên:
                <input required value={newFullName} onChange={e => setNewFullName(e.target.value)} placeholder="vd: Nguyễn Văn A" />
              </label>
              <label>
                Chi nhánh:
                <select value={newBranch} onChange={e => setNewBranch(e.target.value)}>
                  <option value="HN">Hà Nội (HN)</option>
                  <option value="HCM">Hồ Chí Minh (HCM)</option>
                  <option value="DN">Đà Nẵng (DN)</option>
                  <option value="">Toàn hệ thống (Trống)</option>
                </select>
              </label>
              <button type="submit" disabled={loading} className="primary-btn">Tạo User</button>
            </form>
          </div>

          {/* Cột 2: Sửa quyền */}
          <div className="admin-section">
            <h3>Phân Quyền (Row-Level / Masking)</h3>
            <div className="admin-form">
              <label>
                Chọn User:
                <select value={selectedUserId} onChange={e => handleSelectUser(e.target.value)}>
                  <option value="">-- Chọn User --</option>
                  {users.map(u => (
                    <option key={u.id} value={u.id}>{u.full_name} ({u.username})</option>
                  ))}
                </select>
              </label>

              {selectedUserId && (
                <>
                  <label>
                    Truy cập bảng Khách hàng:
                    <select value={tableAccess} onChange={e => setTableAccess(e.target.value)}>
                      <option value="ALLOW">Cho phép (ALLOW)</option>
                      <option value="DENY">Cấm truy cập (DENY)</option>
                    </select>
                  </label>
                  <label>
                    Row Filter (SQL):
                    <input 
                      value={rowFilter} 
                      onChange={e => setRowFilter(e.target.value)} 
                      placeholder="vd: branch_code = '{user.branch_code}'" 
                    />
                    <small>Để trống nếu muốn cho phép truy cập toàn bộ dòng.</small>
                  </label>
                  <label>
                    Cột phone_number:
                    <select value={phoneMask} onChange={e => setPhoneMask(e.target.value)}>
                      <option value="NONE">Không che (NONE)</option>
                      <option value="PARTIAL">Che một phần (***)</option>
                      <option value="HASH">Băm dữ liệu (HASH)</option>
                      <option value="DENY">Cấm truy cập (DENY)</option>
                    </select>
                  </label>
                  <label>
                    Cột id_number:
                    <select value={idMask} onChange={e => setIdMask(e.target.value)}>
                      <option value="NONE">Không che (NONE)</option>
                      <option value="PARTIAL">Che một phần (***)</option>
                      <option value="HASH">Băm dữ liệu (HASH)</option>
                      <option value="DENY">Cấm truy cập (DENY)</option>
                    </select>
                  </label>
                  
                  <button onClick={handleUpdatePermissions} disabled={loading} className="primary-btn">Lưu Quyền</button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
