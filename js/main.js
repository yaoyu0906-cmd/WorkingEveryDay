function getUsername() {
  return localStorage.getItem("wed_username") || "User";
}
 
function goProfile() {
  location.href = '/profile';
}
 