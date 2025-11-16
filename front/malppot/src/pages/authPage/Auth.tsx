import React from "react";
import styles from "./Auth.module.css";

const GoogleLogoSVG = (): React.JSX.Element => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 18 18"
    xmlns="http://www.w3.org/2000/svg"
  >
    <g fill="none" fillRule="evenodd">
      <path
        d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
        fill="#4285F4"
      ></path>
      <path
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z"
        fill="#34A853"
      ></path>
      <path
        d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
        fill="#FBBC05"
      ></path>
      <path
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
        fill="#EA4335"
      ></path>
    </g>
  </svg>
);

import logo from "assets/images/new_malppot.png"; 

const Auth = (): React.JSX.Element => {
    const handleLogin = () => {
        window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?` +
            `client_id=${import.meta.env.VITE_GOOGLE_AUTH_CLIENT_ID}` +
            `&redirect_uri=${import.meta.env.VITE_GOOGLE_AUTH_REDIRECT_URI}` +
            `&response_type=code` +
            `&scope=email profile`;
    };

    return (
        <div className={styles.pageWrapper}>
        <div className={styles.infoPanel}>
            <div className={styles.infoTextContainer}>
            <p className={styles.infoLine}>
                모두의 <span className={styles.highlight}>말</span>이
            </p>
            <p className={styles.infoLine}>
                세상에 <span className={styles.highlight}>뻗</span>어나갈 수 있도록
            </p>
            </div>
        </div>

        <div className={styles.loginPanel}>
            <div className={styles.loginBox}>
            <img src={logo} alt="말뻗 로고" className={styles.logoImage} />
            <p className={styles.subtitle}>Google 계정으로 간편하게 시작하세요.</p>
            
            <button className={styles.googleSignInButton} onClick={handleLogin}>
                <GoogleLogoSVG />
                Google 계정으로 로그인
            </button>

            </div>
        </div>
        </div>
    );
};

export default Auth;