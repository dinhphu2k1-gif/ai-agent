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

interface PermissionRow {
  resource_id: string;
  resource_name: string;
  resource_type: string;
  effect: string;
  row_filter: string | null;
  mask_type: string | null;
}

export function AdminPanel({ onClose, onUserAdded }: AdminPanelProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>('');

  // Create User State
  const [newUsername, setNewUsername] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newBranch, setNewBranch] = useState('HN');

  // Permissions State
  const [permissions, setPermissions] = useState<PermissionRow[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

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

  useEffect(() => {
    if (selectedUserId) {
      loadPermissions(selectedUserId);
    } else {
      setPermissions([]);
    }
  }, [selectedUserId]);

  const loadPermissions = async (userId: string) => {
    setErrorMsg('');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${userId}/permissions`);
      if (res.ok) {
        const data = await res.json();
        setPermissions(data);
      } else {
        setErrorMsg('Lỗi khi tải dữ liệu quyền (500). Vui lòng thử lại.');
      }
    } catch (e) {
      console.error(e);
      setErrorMsg('Lỗi kết nối đến server.');
    }
  };

  const handleSavePermissions = async () => {
    if (!selectedUserId) return;
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${selectedUserId}/permissions`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(permissions)
      });
      if (res.ok) {
        setMessage('Cập nhật quyền thành công!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        setMessage('Cập nhật quyền thất bại.');
      }
    } catch (e) {
      setMessage('Lỗi kết nối.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUsername || !newFullName) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: newUsername,
          full_name: newFullName,
          branch_code: newBranch
        })
      });
      if (res.ok) {
        setNewUsername('');
        setNewFullName('');
        await fetchUsers();
        onUserAdded();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const updatePermission = (index: number, field: keyof PermissionRow, value: string | null) => {
    const newPerms = [...permissions];
    newPerms[index] = { ...newPerms[index], [field]: value };
    setPermissions(newPerms);
  };

  return (
    <div className="admin-overlay">
      <div className="admin-modal" style={{ maxWidth: '1200px', width: '95vw' }}>
        <div className="admin-header">
          <h2>Quản lý Người Dùng & Phân Quyền</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="admin-body">
          {/* Left Column: Create User */}
          <div className="admin-col" style={{ flex: '0 0 250px' }}>
            <h3>1. Tạo User Mới</h3>
            <div className="form-group">
              <label>Username:</label>
              <input value={newUsername} onChange={e => setNewUsername(e.target.value)} placeholder="vd: nv_a" />
              
              <label>Họ và tên:</label>
              <input value={newFullName} onChange={e => setNewFullName(e.target.value)} placeholder="vd: Nguyễn Văn A" />
              
              <label>Chi nhánh:</label>
              <select value={newBranch} onChange={e => setNewBranch(e.target.value)}>
                <option value="HN">Hà Nội (HN)</option>
                <option value="HCM">Hồ Chí Minh (HCM)</option>
                <option value="DN">Đà Nẵng (DN)</option>
                <option value="ALL">Toàn quốc (ALL)</option>
              </select>

              <button className="btn-primary" onClick={handleCreateUser} disabled={loading}>
                {loading ? 'Đang tạo...' : '+ Thêm người dùng'}
              </button>
            </div>
          </div>

          {/* Right Column: Manage Permissions */}
          <div className="admin-col" style={{ flex: 1 }}>
            <h3>2. Cấu Hình Phân Quyền Động</h3>
            <div className="form-group">
              <label>Chọn người dùng để phân quyền:</label>
              <select value={selectedUserId} onChange={e => setSelectedUserId(e.target.value)}>
                <option value="">-- Chọn User --</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>
                    {u.full_name} ({u.username} - {u.branch_code})
                  </option>
                ))}
              </select>

              {selectedUserId && (
                <>
                  {errorMsg ? (
                    <div className="message-error" style={{ color: '#ef4444', marginTop: '16px' }}>{errorMsg}</div>
                  ) : (
                  <div style={{ overflowX: 'auto', marginTop: '16px' }}>
                    <table className="perm-table">
                      <thead>
                        <tr>
                          <th>Resource</th>
                          <th>Type</th>
                          <th>Action</th>
                          <th>Effect</th>
                          <th>Row Filter</th>
                          <th>Column Mask</th>
                        </tr>
                      </thead>
                      <tbody>
                        {permissions.map((p, idx) => (
                          <tr key={p.resource_id}>
                            <td className="code-font">{p.resource_name}</td>
                            <td>{p.resource_type}</td>
                            <td>SELECT</td>
                            <td>
                              <select 
                                value={p.effect} 
                                onChange={e => updatePermission(idx, 'effect', e.target.value)}
                                style={{ minWidth: '100px' }}
                              >
                                <option value="ALLOW">ALLOW</option>
                                <option value="DENY">DENY</option>
                              </select>
                            </td>
                            <td>
                              {(p.resource_type === 'TABLE' || p.resource_type === 'SCHEMA') ? (
                                <input 
                                  className="code-font"
                                  value={p.row_filter || ''} 
                                  onChange={e => updatePermission(idx, 'row_filter', e.target.value || null)}
                                  placeholder="vd: branch_code = 'HN'"
                                  style={{ minWidth: '220px' }}
                                />
                              ) : (
                                <span className="text-muted">—</span>
                              )}
                            </td>
                            <td>
                              {p.resource_type === 'COLUMN' ? (
                                <select 
                                  value={p.mask_type || 'NONE'} 
                                  onChange={e => updatePermission(idx, 'mask_type', e.target.value)}
                                  style={{ minWidth: '120px' }}
                                >
                                  <option value="NONE">NONE</option>
                                  <option value="PARTIAL">PARTIAL</option>
                                  <option value="REDACT">REDACT</option>
                                  <option value="HASH">HASH</option>
                                </select>
                              ) : (
                                <span className="text-muted">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  )}

                  <div className="admin-actions" style={{ marginTop: '20px' }}>
                    {message && <span className="message-success">{message}</span>}
                    <button className="btn-primary" onClick={handleSavePermissions} disabled={loading}>
                      {loading ? 'Đang lưu...' : '💾 Lưu Quyền'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
