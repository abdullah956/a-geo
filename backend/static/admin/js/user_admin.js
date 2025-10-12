function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        // Create a form to submit the deletion request
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = window.location.href;
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add action
        const actionInput = document.createElement('input');
        actionInput.type = 'hidden';
        actionInput.name = 'action';
        actionInput.value = 'delete_selected_users';
        form.appendChild(actionInput);
        
        // Add selected users
        const selectInput = document.createElement('input');
        selectInput.type = 'hidden';
        selectInput.name = '_selected_action';
        selectInput.value = userId;
        form.appendChild(selectInput);
        
        // Add select all
        const selectAllInput = document.createElement('input');
        selectAllInput.type = 'hidden';
        selectAllInput.name = 'select_across';
        selectAllInput.value = '0';
        form.appendChild(selectAllInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}
