// src/components/StockIntelligenceWidget.tsx
/**
 * Stock Intelligence Dashboard Widget
 * 
 * Displays smart stock recommendations for admin dashboard:
 * - Critical alerts (products running out soon)
 * - Seasonal opportunities
 * - Top sellers and low performers
 */

import React, { useEffect, useState } from 'react';
import { stockIntelligenceAPI } from '../services/api';
import {
    AlertTriangle,
    TrendingUp,
    TrendingDown,
    Package,
    CheckCircle,
    AlertCircle,
    RefreshCw,
    ShoppingBag,
    Copy,
    Check,
} from 'lucide-react';

// Types
interface StockAlert {
    product_id: number;
    product_name: string;
    brand: string;
    category: string;
    current_stock: number;
    sales_last_30_days: number;
    velocity: number;
    predicted_monthly_sales: number | null;
    forecast_source: 'forecast' | 'velocity';
    days_until_stockout: number | null;
    recommended_order_qty: number;
    urgency: 'critical' | 'warning' | 'opportunity' | 'dead_stock' | 'healthy';
    message: string;
    estimated_order_cost?: number;
}

interface DashboardSummary {
    summary: {
        critical_count: number;
        warning_count: number;
        opportunity_count: number;
        healthy_count: number;
        total_products: number;
        forecast_model_active: boolean;
    };
    critical_alerts: StockAlert[];
    warning_alerts: StockAlert[];
    opportunities: StockAlert[];
    top_sellers: Array<{ product__name: string; product__brand: string; sales_count: number }>;
    low_performers: Array<{ name: string; brand: string; stock: number; sales_count: number }>;
}

export default function StockIntelligenceWidget() {
    const [data, setData] = useState<DashboardSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'critical' | 'warnings' | 'opportunities' | 'sellers'>('critical');
    const [warningsPage, setWarningsPage] = useState(1);
    const [copiedId, setCopiedId] = useState<number | null>(null);
    const ITEMS_PER_PAGE = 10;

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const response = await stockIntelligenceAPI.getDashboardSummary();
            setData(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to load stock data');
            console.error('Stock Intelligence Error:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY',
            minimumFractionDigits: 0,
        }).format(value);
    };

    const copyOrderToClipboard = (alert: StockAlert) => {
        const text = `${alert.product_name} (${alert.brand}) — ${alert.recommended_order_qty} units`;
        navigator.clipboard.writeText(text).then(() => {
            setCopiedId(alert.product_id);
            setTimeout(() => setCopiedId(null), 2000);
        });
    };

    if (loading) {
        return (
            <div className="bg-white rounded-2xl shadow-sm p-12 flex flex-col items-center justify-center">
                <RefreshCw className="animate-spin text-blue-600 mb-4" size={32} />
                <span className="text-gray-500 font-medium">AI is analyzing stock data...</span>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="bg-red-50 border border-red-100 rounded-2xl p-8 text-center">
                <AlertTriangle className="mx-auto text-red-500 mb-4" size={32} />
                <span className="block text-red-800 font-medium mb-4">{error || 'Failed to load data'}</span>
                <button
                    onClick={fetchData}
                    className="px-6 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors font-medium"
                >
                    Try Again
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header Area */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <div className="flex items-center gap-2">
                        <h2 className="text-xl font-bold text-gray-900">Stock Intelligence</h2>
                        {data.summary.forecast_model_active ? (
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-bold rounded-full">AI Forecast Active</span>
                        ) : (
                            <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs font-medium rounded-full">30-Day Velocity</span>
                        )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">Stock optimization and smart order recommendations</p>
                </div>
                <button
                    onClick={fetchData}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-600 rounded-xl hover:bg-gray-50 transition-colors text-sm font-medium shadow-sm"
                >
                    <RefreshCw size={16} />
                    Refresh Data
                </button>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white rounded-2xl p-5 border border-red-100 shadow-sm relative overflow-hidden group hover:border-red-200 transition-all">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <AlertCircle size={64} className="text-red-600" />
                    </div>
                    <div className="relative z-10">
                        <p className="text-sm font-medium text-red-600 mb-1">Critical Stock</p>
                        <h3 className="text-3xl font-bold text-gray-900">{data.summary.critical_count}</h3>
                        <p className="text-xs text-gray-500 mt-2">Urgent order needed</p>
                    </div>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-yellow-100 shadow-sm relative overflow-hidden group hover:border-yellow-200 transition-all">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <AlertTriangle size={64} className="text-yellow-600" />
                    </div>
                    <div className="relative z-10">
                        <p className="text-sm font-medium text-yellow-600 mb-1">Warnings</p>
                        <h3 className="text-3xl font-bold text-gray-900">{data.summary.warning_count}</h3>
                        <p className="text-xs text-gray-500 mt-2">Needs attention</p>
                    </div>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-green-100 shadow-sm relative overflow-hidden group hover:border-green-200 transition-all">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <TrendingUp size={64} className="text-green-600" />
                    </div>
                    <div className="relative z-10">
                        <p className="text-sm font-medium text-green-600 mb-1">Opportunities</p>
                        <h3 className="text-3xl font-bold text-gray-900">{data.summary.opportunity_count}</h3>
                        <p className="text-xs text-gray-500 mt-2">High sales potential</p>
                    </div>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-blue-100 shadow-sm relative overflow-hidden group hover:border-blue-200 transition-all">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <CheckCircle size={64} className="text-blue-600" />
                    </div>
                    <div className="relative z-10">
                        <p className="text-sm font-medium text-blue-600 mb-1">Healthy Stock</p>
                        <h3 className="text-3xl font-bold text-gray-900">{data.summary.healthy_count}</h3>
                        <p className="text-xs text-gray-500 mt-2">Optimum level</p>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                {/* Tabs */}
                <div className="border-b border-gray-100 px-6 pt-4 flex gap-6 overflow-x-auto">
                    <button
                        onClick={() => setActiveTab('critical')}
                        className={`pb-4 px-2 text-sm font-medium transition-all relative ${activeTab === 'critical'
                                ? 'text-red-600'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Kritik Warnings ({data.critical_alerts.length})
                        {activeTab === 'critical' && (
                            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-red-600 rounded-t-full" />
                        )}
                    </button>
                    <button
                        onClick={() => setActiveTab('warnings')}
                        className={`pb-4 px-2 text-sm font-medium transition-all relative ${activeTab === 'warnings'
                                ? 'text-yellow-600'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Warnings ({data.warning_alerts.length})
                        {activeTab === 'warnings' && (
                            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-yellow-600 rounded-t-full" />
                        )}
                    </button>
                    <button
                        onClick={() => setActiveTab('opportunities')}
                        className={`pb-4 px-2 text-sm font-medium transition-all relative ${activeTab === 'opportunities'
                                ? 'text-green-600'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Opportunity Products ({data.opportunities.length})
                        {activeTab === 'opportunities' && (
                            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-green-600 rounded-t-full" />
                        )}
                    </button>
                    <button
                        onClick={() => setActiveTab('sellers')}
                        className={`pb-4 px-2 text-sm font-medium transition-all relative ${activeTab === 'sellers'
                                ? 'text-blue-600'
                                : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Sales Analysis
                        {activeTab === 'sellers' && (
                            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-600 rounded-t-full" />
                        )}
                    </button>
                </div>

                {/* Tab Content */}
                <div className="p-6 bg-gray-50/50 min-h-[400px]">

                    {/* CRITICAL ALERTS TAB */}
                    {activeTab === 'critical' && (
                        <div className="space-y-4">
                            {data.critical_alerts.length === 0 ? (
                                <EmptyState message="Great! No critical stock alerts." icon={CheckCircle} color="text-green-500" />
                            ) : (
                                data.critical_alerts.map((alert) => (
                                    <div key={alert.product_id} className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow flex flex-col md:flex-row gap-6">
                                        <div className="flex-1">
                                            <div className="flex items-start justify-between mb-2">
                                                <div className="flex items-center gap-2">
                                                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                                                    <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full uppercase tracking-wider">Urgent</span>
                                                </div>
                                                <span className="text-xs text-gray-400 font-medium">{alert.category}</span>
                                            </div>
                                            <h4 className="font-bold text-gray-900 text-lg mb-1">{alert.product_name}</h4>
                                            <p className="text-sm text-gray-500 mb-4">{alert.brand}</p>

                                            <div className="flex flex-wrap gap-4 text-sm">
                                                <div className="bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                                    <span className="text-gray-500 block text-xs">Current Stock</span>
                                                    <span className="font-bold text-gray-900">{alert.current_stock} Units</span>
                                                </div>
                                                <div className="bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                                    <span className="text-gray-500 block text-xs">Time Remaining</span>
                                                    <span className={`font-bold ${!alert.days_until_stockout ? 'text-red-600' : 'text-gray-900'}`}>
                                                        {alert.days_until_stockout ? `${Math.round(alert.days_until_stockout)} Days` : 'Out of Stock!'}
                                                    </span>
                                                </div>
                                                <div className="bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100">
                                                    <span className="text-blue-600 block text-xs">Sales Velocity</span>
                                                    <span className="font-bold text-blue-800">{alert.velocity.toFixed(1)} / day</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="md:w-72 bg-gray-50 rounded-xl p-4 border border-gray-100 flex flex-col justify-center">
                                            <div className="flex items-center gap-2 mb-3 text-sm font-medium text-gray-700">
                                                <ShoppingBag size={16} />
                                                Recommended Order
                                                {alert.forecast_source === 'forecast' && (
                                                    <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-medium">AI</span>
                                                )}
                                            </div>
                                            <div className="flex justify-between items-end mb-2">
                                                <span className="text-2xl font-bold text-gray-900">{alert.recommended_order_qty} <span className="text-base font-normal text-gray-500">Units</span></span>
                                                <span className="text-sm font-bold text-gray-900">{alert.estimated_order_cost != null ? formatCurrency(alert.estimated_order_cost) : '-'}</span>
                                            </div>
                                            <button
                                                onClick={() => copyOrderToClipboard(alert)}
                                                className="w-full mt-2 bg-gray-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
                                            >
                                                {copiedId === alert.product_id ? (
                                                    <><Check size={14} /> Copied</>
                                                ) : (
                                                    <><Copy size={14} /> Copy Order</>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {/* WARNING ALERTS TAB */}
                    {activeTab === 'warnings' && (
                        <div className="space-y-4">
                            {data.warning_alerts.length === 0 ? (
                                <EmptyState message="No yellow alert warnings to follow." icon={CheckCircle} color="text-green-500" />
                            ) : (
                                <>
                                {data.warning_alerts.slice((warningsPage - 1) * ITEMS_PER_PAGE, warningsPage * ITEMS_PER_PAGE).map((alert) => (
                                    <div key={alert.product_id} className="bg-white rounded-xl p-5 border border-yellow-200 shadow-sm hover:shadow-md transition-shadow flex flex-col md:flex-row gap-6">
                                        <div className="flex-1">
                                            <div className="flex items-start justify-between mb-2">
                                                <div className="flex items-center gap-2">
                                                    <AlertTriangle size={16} className="text-yellow-500" />
                                                    <span className="text-xs font-bold text-yellow-700 bg-yellow-50 px-2 py-0.5 rounded-full uppercase tracking-wider">Warning</span>
                                                </div>
                                                <span className="text-xs text-gray-400 font-medium">{alert.category}</span>
                                            </div>
                                            <h4 className="font-bold text-gray-900 text-lg mb-1">{alert.product_name}</h4>
                                            <p className="text-sm text-gray-500 mb-4">{alert.brand} - {alert.message}</p>

                                            <div className="flex flex-wrap gap-4 text-sm">
                                                <div className="bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                                    <span className="text-gray-500 block text-xs">Current Stock</span>
                                                    <span className="font-bold text-gray-900">{alert.current_stock} Units</span>
                                                </div>
                                                <div className="bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                                    <span className="text-gray-500 block text-xs">Est. Stockout</span>
                                                    <span className="font-bold text-yellow-700">
                                                        {alert.days_until_stockout ? `${Math.round(alert.days_until_stockout)} Days` : '-'}
                                                    </span>
                                                </div>
                                                <div className="bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100">
                                                    <span className="text-blue-600 block text-xs">Sales Velocity</span>
                                                    <span className="font-bold text-blue-800">{alert.velocity.toFixed(1)} / day</span>
                                                </div>
                                            </div>
                                        </div>
                                        {alert.recommended_order_qty > 0 && (
                                            <div className="md:w-64 bg-yellow-50 rounded-xl p-4 border border-yellow-100 flex flex-col justify-center">
                                                <div className="flex items-center gap-2 mb-3 text-sm font-medium text-yellow-800">
                                                    <ShoppingBag size={16} />
                                                    Recommended Order
                                                    {alert.forecast_source === 'forecast' && (
                                                        <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-medium">AI</span>
                                                    )}
                                                </div>
                                                <div className="flex justify-between items-end mb-2">
                                                    <span className="text-2xl font-bold text-gray-900">{alert.recommended_order_qty} <span className="text-base font-normal text-gray-500">Units</span></span>
                                                    <span className="text-sm font-bold text-gray-900">{alert.estimated_order_cost != null ? formatCurrency(alert.estimated_order_cost) : '-'}</span>
                                                </div>
                                                <button
                                                    onClick={() => copyOrderToClipboard(alert)}
                                                    className="w-full mt-2 bg-yellow-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-yellow-700 transition-colors flex items-center justify-center gap-2"
                                                >
                                                    {copiedId === alert.product_id ? (
                                                        <><Check size={14} /> Copied</>
                                                    ) : (
                                                        <><Copy size={14} /> Copy Order</>
                                                    )}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                ))}
                                {Math.ceil(data.warning_alerts.length / ITEMS_PER_PAGE) > 1 && (
                                    <div className="flex justify-center items-center gap-4 mt-6 pt-4 border-t border-gray-100">
                                        <button 
                                            disabled={warningsPage === 1}
                                            onClick={() => setWarningsPage(p => p - 1)}
                                            className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-all"
                                        >
                                            Previous
                                        </button>
                                        <span className="text-sm text-gray-500 font-medium">
                                            Page {warningsPage} / {Math.ceil(data.warning_alerts.length / ITEMS_PER_PAGE)}
                                        </span>
                                        <button 
                                            disabled={warningsPage === Math.ceil(data.warning_alerts.length / ITEMS_PER_PAGE)}
                                            onClick={() => setWarningsPage(p => p + 1)}
                                            className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-all"
                                        >
                                            Next
                                        </button>
                                    </div>
                                )}
                                </>
                            )}
                        </div>
                    )}

                    {/* OPPORTUNITIES TAB */}
                    {activeTab === 'opportunities' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {data.opportunities.length === 0 ? (
                                <div className="col-span-2">
                                    <EmptyState message="No special opportunity recommendations at the moment." icon={TrendingUp} color="text-blue-500" />
                                </div>
                            ) : (
                                data.opportunities.map((opp) => {
                                    const isDeadStock = opp.urgency === 'dead_stock';
                                    return (
                                        <div key={opp.product_id} className={`bg-white p-5 rounded-xl border shadow-sm relative overflow-hidden ${isDeadStock ? 'border-gray-300' : 'border-gray-200'}`}>
                                            <div className="absolute top-0 right-0 p-3 opacity-5">
                                                {isDeadStock ? <TrendingDown size={100} /> : <TrendingUp size={100} />}
                                            </div>
                                            <div className="relative z-10">
                                                <div className="flex items-center gap-2 mb-3">
                                                    {isDeadStock ? (
                                                        <>
                                                            <span className="bg-gray-100 text-gray-600 p-1.5 rounded-lg">
                                                                <Package size={18} />
                                                            </span>
                                                            <span className="text-xs font-bold text-gray-600 uppercase">Dead Stock</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <span className="bg-green-100 text-green-700 p-1.5 rounded-lg">
                                                                <TrendingUp size={18} />
                                                            </span>
                                                            <span className="text-xs font-bold text-green-700 uppercase">Sales Opportunity</span>
                                                        </>
                                                    )}
                                                    <span className="ml-auto text-xs text-gray-400">{opp.category}</span>
                                                </div>
                                                <h4 className="font-bold text-gray-900 mb-1">{opp.product_name}</h4>
                                                <p className="text-xs text-gray-400 mb-2">{opp.brand}</p>
                                                <p className="text-sm text-gray-500 mb-4">{opp.message}</p>
                                                <div className="flex items-center gap-4 text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                                                    <span>Stock: <strong>{opp.current_stock} units</strong></span>
                                                    <span>Son 30 Days: <strong>{opp.sales_last_30_days} sales</strong></span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    )}

                    {/* SELLERS TAB */}
                    {activeTab === 'sellers' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                                <div className="p-4 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
                                    <h4 className="font-bold text-gray-900 flex items-center gap-2">
                                        <TrendingUp size={18} className="text-green-600" />
                                        Top Sellers
                                    </h4>
                                    <span className="text-xs text-gray-500">Son 30 Days</span>
                                </div>
                                <div className="divide-y divide-gray-100">
                                    {data.top_sellers.map((seller, idx) => (
                                        <div key={idx} className="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${idx === 0 ? 'bg-yellow-100 text-yellow-700' :
                                                    idx === 1 ? 'bg-gray-100 text-gray-600' :
                                                        idx === 2 ? 'bg-orange-50 text-orange-700' : 'bg-gray-50 text-gray-400'
                                                }`}>
                                                {idx + 1}
                                            </div>
                                            <div className="flex-1">
                                                <p className="font-medium text-gray-900 text-sm">{seller.product__name}</p>
                                                <p className="text-xs text-gray-500">{seller.product__brand}</p>
                                            </div>
                                            <div className="text-right">
                                                <span className="block font-bold text-green-600">{seller.sales_count}</span>
                                                <span className="text-xs text-gray-400">Units</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                                <div className="p-4 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
                                    <h4 className="font-bold text-gray-900 flex items-center gap-2">
                                        <TrendingDown size={18} className="text-red-500" />
                                        Low Performance
                                    </h4>
                                    <span className="text-xs text-gray-500">En Az Satanlar (Son 30 Days)</span>
                                </div>
                                <div className="divide-y divide-gray-100">
                                    {data.low_performers.map((low, idx) => (
                                        <div key={idx} className="p-4 flex items-center gap-4 hover:bg-gray-50 transition-colors">
                                            <div className="w-8 h-8 rounded-full bg-red-50 text-red-500 flex items-center justify-center font-bold text-sm">
                                                {idx + 1}
                                            </div>
                                            <div className="flex-1">
                                                <p className="font-medium text-gray-900 text-sm">{low.name}</p>
                                                <p className="text-xs text-gray-500">{low.brand} • Stock: {low.stock}</p>
                                            </div>
                                            <div className="text-right">
                                                <span className="block font-bold text-gray-900">{low.sales_count}</span>
                                                <span className="text-xs text-gray-400">Units Satış</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

const EmptyState = ({ message, icon: Icon, color }: { message: string, icon: any, color: string }) => (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-white rounded-xl border border-dashed border-gray-300">
        <div className={`p-4 rounded-full bg-gray-50 mb-3 ${color}`}>
            <Icon size={32} />
        </div>
        <p className="text-gray-500 font-medium">{message}</p>
    </div>
);
