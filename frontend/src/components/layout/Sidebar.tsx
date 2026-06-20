import { NavLink } from 'react-router-dom';

const links = [
  { to: '/dashboard', label: '📊 仪表盘' },
  { to: '/news', label: '📰 新闻列表' },
  { to: '/technical', label: '📈 技术面' },
  { to: '/filters', label: '🔧 过滤器' },
  { to: '/settings', label: '⚙️ 设置' },
];

export default function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 text-white flex flex-col h-screen">
      <div className="px-5 py-5 border-b border-gray-700">
        <h1 className="text-lg font-bold tracking-tight">News Service</h1>
        <p className="text-xs text-gray-400 mt-0.5">新闻采集与发布管理</p>
      </div>
      <nav className="flex-1 py-4">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `block px-5 py-2.5 text-sm font-medium transition-colors ${
                isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-4 border-t border-gray-700 text-xs text-gray-500">
        v0.1.0
      </div>
    </aside>
  );
}
