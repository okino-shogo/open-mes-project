import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation, Outlet } from 'react-router-dom';
import './App.css';
import authFetch from './utils/api.js';
import Header from './components/Header.jsx';
import SideMenu from './components/SideMenu.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import LoginPage from './pages/LoginPage.jsx';
import VersionModal from './components/VersionModal.jsx';
import TopPage from './pages/TopPage.jsx';
import InventoryInquiry from './pages/InventoryInquiry.jsx';
import StockMovementHistory from './pages/StockMovementHistory.jsx';
import ShipmentSchedule from './pages/ShipmentSchedule.jsx';
import GoodsReceipt from './pages/GoodsReceipt.jsx';
import GoodsIssue from './pages/GoodsIssue.jsx';
import ProductionPlan from './pages/ProductionPlan.jsx';
import ProductionPlanSearchGantt from './pages/ProductionPlanSearchGantt.jsx';
import WorkerInterfaceList from './pages/WorkerInterfaceList.jsx';
import PartsUsed from './pages/PartsUsed.jsx';
import MaterialAllocation from './pages/MaterialAllocation.jsx';
import WorkProgress from './pages/WorkProgress.jsx';
import ProcessInspection from './pages/ProcessInspection.jsx';
import AcceptanceInspection from './pages/AcceptanceInspection.jsx';
import QualityMasterCreation from './pages/QualityMasterCreation.jsx';
import StartInspection from './pages/StartInspection.jsx';
import InspectionHistory from './pages/InspectionHistory.jsx';
import MachineMasterCreation from './pages/MachineMasterCreation.jsx';
import DataImport from './pages/DataImport.jsx';
import UserSettings from './pages/UserSettings.jsx';
import UserManagement from './pages/UserManagement.jsx';
import UserCreate from './pages/UserCreate.jsx';
import UserEdit from './pages/UserEdit.jsx';
import SystemSettings from './pages/SystemSettings.jsx';
import CsvMappingSettings from './pages/CsvMappingSettings.jsx';
import ModelDisplaySettings from './pages/ModelDisplaySettings.jsx';
import PageDisplaySettings from './pages/PageDisplaySettings.jsx';
import QrCodeActionSettings from './pages/QrCodeActionSettings.jsx';
import ShelfQrCodeCreation from './pages/ShelfQrCodeCreation.jsx';
import WorkerPerformanceList from './pages/WorkerPerformanceList.jsx';
import WorkerPerformanceDetail from './pages/WorkerPerformanceDetail.jsx';
import MobileLayout from './layouts/MobileLayout.jsx';
import MobileTopPage from './pages/MobileTopPage.jsx';
import MobileGoodsReceiptPage from './pages/mobile/MobileGoodsReceiptPage.jsx';
import MobileGoodsIssuePage from './pages/mobile/MobileGoodsIssuePage.jsx';
import MobileLocationTransferPage from './pages/mobile/MobileLocationTransferPage.jsx';
import MobileLoginPage from './pages/mobile/MobileLoginPage.jsx';
import Help from './pages/Help.jsx';

// モバイル専用リダイレクト処理
const MobileRedirector = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const path = location.pathname;
    const isMobilePath = path.startsWith('/mobile');
    const isLoginPath = path === '/login';

    if (isMobile) {
      // モバイル端末かつデスクトップ用ログインならモバイルログインへ
      if (isLoginPath) {
        navigate('/mobile/login', { replace: true });
        return;
      }
      // モバイル端末かつモバイル以外のページならモバイルトップへ
      if (!isMobilePath) {
        navigate('/mobile', { replace: true });
        return;
      }
    }

    if (!isMobile && isMobilePath) {
      // デスクトップ端末かつモバイルページならPCトップへ
      navigate('/', { replace: true });
      return;
    }
  }, [location.pathname, navigate]);

  return null;
};

function AppContent() {
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('access_token'));
  const [isStaff, setIsStaff] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [versionModalOpen, setVersionModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsAuthenticated(false);
    setIsStaff(false);
  }, []);

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      setIsAuthenticated(false);
      setIsStaff(false);
      return;
    }

    try {
      const res = await authFetch('/api/users/session/');
      if (res.ok) {
        const json = await res.json();
        setIsAuthenticated(json.isAuthenticated);
        setIsStaff(json.isStaff || json.isSuperuser);
      } else {
        handleLogout();
      }
    } catch (e) {
      console.error("Auth check failed:", e);
      handleLogout();
    } finally {
      setLoading(false);
    }
  }, [handleLogout]);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  useEffect(() => {
    window.addEventListener('logout', handleLogout);
    return () => window.removeEventListener('logout', handleLogout);
  }, [handleLogout]);

  const onLoginSuccess = async () => { await checkAuth(); };

  const toggleMenu = () => setMenuOpen(prev => !prev);
  const closeMenu = () => setMenuOpen(false);

  useEffect(() => {
    document.body.classList.toggle('menu-open-no-scroll', menuOpen);
    return () => { document.body.classList.remove('menu-open-no-scroll'); };
  }, [menuOpen]);

  if (loading) return <div>Loading...</div>;

  const StaffRoute = ({ children }) => {
    if (!isStaff) {
      // スタッフでない場合はトップページにリダイレクト
      return <Navigate to="/" replace />;
    }
    return children;
  };

  return (
    <>      
      <MobileRedirector />

      <Routes>
        {/* Public Login Routes */}
        <Route
          path="/login"
          element={<LoginPage onLoginSuccess={onLoginSuccess} isAuthenticated={isAuthenticated} />
          }
        />
        <Route
          path="/mobile/login"
          element={<MobileLoginPage onLoginSuccess={onLoginSuccess} isAuthenticated={isAuthenticated} />
          }
        />

        {/* Desktop Protected Routes with Layout */}
        <Route
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <>
                <Header onMenuClick={toggleMenu} isMenuOpen={menuOpen} isAuthenticated={isAuthenticated} />
                <SideMenu
                  isOpen={menuOpen}
                  isStaffOrSuperuser={isStaff}
                  onVersionClick={() => setVersionModalOpen(true)}
                  onLinkClick={closeMenu}
                  onLogout={handleLogout}
                  isAuthenticated={isAuthenticated}
                />
                {menuOpen && <div id="menu-overlay" onClick={closeMenu} />}
                <main className='main-contents container'>
                  <Outlet />
                </main>
              </>
            </ProtectedRoute>
          }
        >
          {/* Desktop Protected Routes */}
          <Route path="/" element={<TopPage isStaffOrSuperuser={isStaff} isAuthenticated={isAuthenticated} onLogout={handleLogout} />} />
          <Route path="/inventory/inquiry" element={<InventoryInquiry />} />
          <Route path="/inventory/stock-movement-history" element={<StockMovementHistory />} />
          <Route path="/inventory/shipment" element={<ShipmentSchedule />} />
          <Route path="/inventory/purchase" element={<GoodsReceipt />} />
          <Route path="/inventory/issue" element={<GoodsIssue />} />
          <Route path="/production/plan" element={<ProductionPlan />} />
          <Route path="/production/plan-gantt" element={<ProductionPlanSearchGantt />} />
          <Route path="/production/worker-interface" element={<WorkerInterfaceList />} />
          <Route path="/production/parts-used" element={<PartsUsed />} />
          <Route path="/production/material-allocation" element={<MaterialAllocation />} />
          <Route path="/production/work-progress" element={<WorkProgress />} />
          <Route path="/quality/process-inspection" element={<ProcessInspection />} />
          <Route path="/quality/acceptance-inspection" element={<AcceptanceInspection />} />
          <Route path="/quality/master-creation" element={<QualityMasterCreation />} />
          <Route path="/machine/start-inspection" element={<StartInspection />} />
          <Route path="/machine/inspection-history" element={<InspectionHistory />} />
          <Route path="/machine/master-creation" element={<MachineMasterCreation />} />
          <Route path="/data/import" element={<DataImport />} />
          <Route path="/user/settings" element={<UserSettings />} />
          <Route path="/user/management" element={<StaffRoute><UserManagement /></StaffRoute>} />
          <Route path="/admin/users/create" element={<StaffRoute><UserCreate /></StaffRoute>} />
          <Route path="/admin/users/edit/:id" element={<StaffRoute><UserEdit /></StaffRoute>} />
          <Route path="/system/settings" element={<StaffRoute><SystemSettings /></StaffRoute>} />
          <Route path="/system/csv-mappings" element={<StaffRoute><CsvMappingSettings /></StaffRoute>} />
          <Route path="/system/model-display-settings" element={<StaffRoute><ModelDisplaySettings /></StaffRoute>} />
          <Route path="/system/page-display-settings" element={<StaffRoute><PageDisplaySettings /></StaffRoute>} />
          <Route path="/system/qr-code-actions" element={<StaffRoute><QrCodeActionSettings /></StaffRoute>} />
          <Route path="/system/shelf-qr-code" element={<StaffRoute><ShelfQrCodeCreation /></StaffRoute>} />
          <Route path="/system/worker-performance" element={<StaffRoute><WorkerPerformanceList /></StaffRoute>} />
          <Route path="/system/worker-performance/:workerId" element={<StaffRoute><WorkerPerformanceDetail /></StaffRoute>} />
          <Route path="/help" element={<Help />} />
        </Route>

        {/* Mobile Protected Routes */}
        <Route element={<ProtectedRoute isAuthenticated={isAuthenticated}><MobileLayout onLogout={handleLogout} /></ProtectedRoute>}>
          <Route path="/mobile" element={<MobileTopPage />} />
          <Route path="/mobile/goods-receipt" element={<MobileGoodsReceiptPage />} />
          <Route path="/mobile/goods-issue" element={<MobileGoodsIssuePage />} />
          <Route path="/mobile/location-transfer" element={<MobileLocationTransferPage />} />
        </Route>
      </Routes>

      <VersionModal isOpen={versionModalOpen} onClose={() => setVersionModalOpen(false)} />
    </>
  );
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}
