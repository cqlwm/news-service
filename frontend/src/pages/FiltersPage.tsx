import { useFilters } from '../hooks/useFilters';
import FilterList from '../components/filters/FilterList';
import AddFilterForm from '../components/filters/AddFilterForm';
import Loading from '../components/common/Loading';

export default function FiltersPage() {
  const { filters, loading, add, remove } = useFilters();

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-6">🔧 过滤器管理</h2>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-900 mb-4">当前过滤器</h3>
          {loading ? <Loading /> : <FilterList filters={filters} onRemove={remove} />}
        </div>

        <AddFilterForm onAdd={add} />
      </div>
    </div>
  );
}
