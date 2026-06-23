// Auth guard: verify session with backend before rendering admin page
(async function checkAdminAuth() {
  const API_BASE = window.API_BASE || (location.protocol + '//' + location.hostname + ':4000');
  try {
    const res = await fetch(`${API_BASE}/auth/session`, { credentials: 'include' });
    if (!res.ok) {
      window.location.replace('./index.html');
    }
  } catch (e) {
    console.error('Auth check failed:', e);
    window.location.replace('./index.html');
  }
})();


//run code after page loads
document.addEventListener('DOMContentLoaded', function() {
//grab elements from the page
   const tabBtns = document.querySelectorAll('.tab-btn');
  const itemsTableBody = document.getElementById('itemsTableBody');
  const claimsTableBody = document.getElementById('claimsTableBody');
  const alertContainer = document.getElementById('alertContainer');
  const detailModal = document.getElementById('detailModal');
  const closeDetailModal = document.getElementById('closeDetailModal');
  const detailContent = document.getElementById('detailContent');


//store items and claims
  let allItems = [];
  let allClaims = [];


//load items and claims from the system
  loadData();


//get data from backend or localstorage
  async function loadData() {
      try {
          allItems = await getAllItems();
          allClaims = await getAllClaims();
          updateStats();
          renderItems();
          renderClaims();
      } catch (error) {
          console.error('Error loading data:', error);
          showAlert('Error loading data. Please refresh the page.', 'error');
      }
  }


//update dashbaord
  function updateStats() {
      document.getElementById('totalItems').textContent = allItems.length;
      document.getElementById('pendingItems').textContent = allItems.filter(i => i.status === 'pending').length;
      document.getElementById('approvedItems').textContent = allItems.filter(i => i.status === 'approved').length;
      document.getElementById('totalClaims').textContent = allClaims.length;
  }


//show all items in admin table
  function renderItems() {
      if (allItems.length === 0) {
          itemsTableBody.innerHTML = '<tr><td colspan="6" class="empty-state">No items reported yet.</td></tr>';
          return;
      }




      itemsTableBody.innerHTML = allItems.map(item => `
          <tr>
              <td>
                  <strong>${escapeHtml(item.name)}</strong>
                  <br><small style="color: #53629E;">by ${escapeHtml(item.finder_name)}</small>
              </td>
              <td>${escapeHtml(item.category)}</td>
              <td>${escapeHtml(item.location)}</td>
              <td>${formatDate(item.date_found)}</td>
              <td><span class="item-status status-${item.status}">${capitalize(item.status)}</span></td>
              <td>
                  <div class="admin-actions">
                      <button class="btn-small btn-approve" onclick="viewItemDetails('${item.id}')">View</button>
                      ${item.status === 'pending' ? `<button class="btn-small btn-approve" onclick="approveItem('${item.id}')">Approve</button>` : ''}
                      <button class="btn-small btn-delete" onclick="deleteItemConfirm('${item.id}')">Delete</button>
                  </div>
              </td>
          </tr>
      `).join('');
  }


//show all claims in admin table
  function renderClaims() {
      if (allClaims.length === 0) {
          claimsTableBody.innerHTML = '<tr><td colspan="6" class="empty-state">No claims submitted yet.</td></tr>';
          return;
      }




      claimsTableBody.innerHTML = allClaims.map(claim => `
          <tr>
              <td><strong>${escapeHtml(claim.claimant_name)}</strong></td>
              <td>${escapeHtml(claim.item_name)}</td>
              <td>${escapeHtml(claim.claimant_email)}</td>
              <td>${formatDate(claim.created_at)}</td>
              <td><span class="item-status status-${claim.status}">${capitalize(claim.status)}</span></td>
              <td>
                  <div class="admin-actions">
                      <button class="btn-small btn-approve" onclick="viewClaimDetails('${claim.id}')">View</button>
                      ${claim.status === 'pending' ? `
                          <button class="btn-small btn-approve" onclick="approveClaim('${claim.id}')">Approve</button>
                          <button class="btn-small btn-delete" onclick="rejectClaim('${claim.id}')">Reject</button>
                      ` : ''}
                  </div>
              </td>
          </tr>
      `).join('');
  }


//hande swithcing between items and claims
  tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
          tabBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');




          const tab = btn.dataset.tab;
          document.getElementById('itemsTab').style.display = tab === 'items' ? 'block' : 'none';
          document.getElementById('claimsTab').style.display = tab === 'claims' ? 'block' : 'none';
      });
  });


//show item details in popup
  window.viewItemDetails = function(id) {
      const item = allItems.find(i => i.id === id || i.id === parseInt(id));
      if (!item) return;




      detailContent.innerHTML = `
          <h2 style="color: #473472; margin-bottom: 20px;">Item Details</h2>
          ${item.image_url ? `<img src="${item.image_url}" alt="${item.name}" style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 15px; margin-bottom: 20px;">` : ''}
          <p><strong>Name:</strong> ${escapeHtml(item.name)}</p>
          <p><strong>Category:</strong> ${escapeHtml(item.category)}</p>
          <p><strong>Location:</strong> ${escapeHtml(item.location)}</p>
          <p><strong>Date Found:</strong> ${formatDate(item.date_found)}</p>
          <p><strong>Description:</strong> ${escapeHtml(item.description)}</p>
          <p><strong>Finder:</strong> ${escapeHtml(item.finder_name)} (${escapeHtml(item.finder_email)})</p>
          <p><strong>Status:</strong> <span class="item-status status-${item.status}">${capitalize(item.status)}</span></p>
      `;
      detailModal.classList.add('active');
  };


//show claim details in popup
  window.viewClaimDetails = function(id) {
      const claim = allClaims.find(c => c.id === id || c.id === parseInt(id));
      if (!claim) return;




      detailContent.innerHTML = `
          <h2 style="color: #473472; margin-bottom: 20px;">Claim Details</h2>
          <p><strong>Claimant:</strong> ${escapeHtml(claim.claimant_name)}</p>
          <p><strong>Email:</strong> ${escapeHtml(claim.claimant_email)}</p>
          <p><strong>Phone:</strong> ${escapeHtml(claim.claimant_phone || 'Not provided')}</p>
          <p><strong>Item:</strong> ${escapeHtml(claim.item_name)}</p>
          <p><strong>Proof of Ownership:</strong></p>
          <p style="background: rgba(135, 186, 195, 0.1); padding: 15px; border-radius: 10px;">${escapeHtml(claim.description)}</p>
          <p><strong>Submitted:</strong> ${formatDate(claim.created_at)}</p>
          <p><strong>Status:</strong> <span class="item-status status-${claim.status}">${capitalize(claim.status)}</span></p>
      `;
      detailModal.classList.add('active');
  };


//approve an item
  window.approveItem = async function(id) {
      try {
          await updateItemStatus(id, 'approved');
          showAlert('Item approved successfully!', 'success');
          loadData();
      } catch (error) {
          console.error('Error approving item:', error);
          showAlert('Error approving item.', 'error');
      }
  };


//delete an item
  window.deleteItemConfirm = async function(id) {
      if (confirm('Are you sure you want to delete this item?')) {
          try {
              await deleteItem(id);
              showAlert('Item deleted successfully!', 'success');
              loadData();
          } catch (error) {
              console.error('Error deleting item:', error);
              showAlert('Error deleting item.', 'error');
          }
      }
  };


//appprove a claim
  window.approveClaim = async function(id) {
      try {
          await updateClaimStatus(id, 'approved');
          showAlert('Claim approved! Contact the claimant to arrange item pickup.', 'success');
          loadData();
      } catch (error) {
          console.error('Error approving claim:', error);
          showAlert('Error approving claim.', 'error');
      }
  };


//reect a claim
  window.rejectClaim = async function(id) {
      if (confirm('Are you sure you want to reject this claim?')) {
          try {
              await updateClaimStatus(id, 'rejected');
              showAlert('Claim rejected.', 'success');
              loadData();
          } catch (error) {
              console.error('Error rejecting claim:', error);
              showAlert('Error rejecting claim.', 'error');
          }
      }
  };


//close popup
  closeDetailModal.addEventListener('click', () => {
      detailModal.classList.remove('active');
  });




  detailModal.addEventListener('click', (e) => {
      if (e.target === detailModal) {
          detailModal.classList.remove('active');
      }
  });


//temparary message at the top
  function showAlert(message, type) {
      alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
      setTimeout(() => {
          alertContainer.innerHTML = '';
      }, 5000);
  }




  function escapeHtml(text) {
      if (!text) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
  }




  function formatDate(dateString) {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString('en-US', options);
  }




  function capitalize(str) {
      return str.charAt(0).toUpperCase() + str.slice(1);
  }
});






