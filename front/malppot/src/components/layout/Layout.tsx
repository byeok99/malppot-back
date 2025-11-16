import React, { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "store/index"; // RootState 경로 확인
import { Outlet } from 'react-router-dom';

import { clearAccessToken } from 'store/authSlice';
import authApi from 'apis/authApi';

import { useNavigator } from 'hooks/useNavigator';

import logo from 'assets/images/new_malppot.png';
import styles from './Layout.module.css';

import HeaderNav from 'components/layout/HeaderNav';

const Layout = (): React.JSX.Element => {
    const { goHome, goAuth, goMy } = useNavigator();
    const dispatch = useDispatch();

    const accessToken = useSelector((state: RootState) => state.auth.accessToken);
    const name = useSelector((state: RootState) => state.auth.name);
    const profile_image_url = useSelector((state: RootState) => state.auth.profile_image_url);

    const isLoggedIn = !!accessToken;

    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const defaultProfileImage = "https://png.pngtree.com/png-vector/20191110/ourlarge/pngtree-avatar-icon-profile-icon-member-login-vector-isolated-png-image_1978396.jpg";

    const handleLogout = async () => {
        try {
            await authApi.logout();
        } finally {
            dispatch(clearAccessToken());
            setIsDropdownOpen(false);
            goHome();
        }
    };

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <>
            <header className={styles.headerWrapper}>
                <div className={styles.leftSection}>
                    <img
                        src={logo}
                        alt="[말:뻗] 로고"
                        className={styles.logo}
                        onClick={goHome}
                    />
                </div>

                <HeaderNav isLogin={isLoggedIn} />

                <div className={styles.rightSection}>
                    {isLoggedIn ? (
                        <div
                            ref={dropdownRef}
                            className={styles.profileContainer}
                            onClick={() => setIsDropdownOpen((prev) => !prev)}
                        >
                            <div className={styles.profileDisplay}>
                                <p className={styles.userName}>{name}</p>
                                <img
                                    src={profile_image_url || defaultProfileImage}
                                    alt="User Profile"
                                    className={styles.profileImage}
                                />
                            </div>
                            <div className={`${styles.dropdownMenu} ${isDropdownOpen ? styles.open : ''}`}>
                                <div className={styles.dropdownItem} onClick={handleLogout}>
                                    로그아웃
                                </div>
                                <div className={`${styles.dropdownItem} ${styles.dropdownMypage}`} onClick={goMy}>
                                    마이페이지
                                </div>
                            </div>
                        </div>
                    ) : (
                        <button className={styles.authButton} onClick={goAuth}>
                            로그인
                        </button>
                    )}
                </div>
            </header>
            <Outlet />
        </>
    );
};

export default Layout;